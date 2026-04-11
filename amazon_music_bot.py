import os
import re
import json
import asyncio
import subprocess

import httpx
from pyrogram import Client, filters, idle
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)
from pyrogram.enums import ParseMode, ButtonStyle

import config
import mongodb


DOWNLOAD_DIR = "./downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/134.0.0.0 Safari/537.36"
)

AMAZON_URL_RE = re.compile(
    r"https?://music\.amazon\.(in|com|co\.uk|de|jp|fr|ca|com\.au)/\S+"
)


def is_amazon_url(text: str) -> bool:
    return bool(AMAZON_URL_RE.search(text))


def extract_asin(url: str) -> str:
    from urllib.parse import urlparse, parse_qs

    parsed = urlparse(url)
    qs = parse_qs(parsed.query)

    if qs.get("trackAsin"):
        candidate = qs["trackAsin"][0]
        if re.match(r"^B[0-9A-Z]{9}$", candidate):
            return candidate

    match = re.search(r"(B[0-9A-Z]{9})", parsed.path or url)
    if not match:
        raise ValueError("couldn't find a track ASIN in that url")

    return match.group(1)


def probe_audio(path: str) -> dict:
    result = subprocess.run(
        [
            "ffprobe", "-v", "quiet",
            "-select_streams", "a:0",
            "-show_entries", "stream=codec_name,bits_per_raw_sample,sample_rate",
            "-of", "json",
            path,
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError("ffprobe failed — is ffmpeg installed and in PATH?")

    streams = json.loads(result.stdout).get("streams", [])
    if not streams:
        raise RuntimeError("ffprobe found no audio streams — file might be corrupt")

    return streams[0]


async def fetch_track_meta(asin: str) -> dict:
    async with httpx.AsyncClient(
        headers={"User-Agent": USER_AGENT}, timeout=30
    ) as client:
        resp = await client.get(f"{config.API_BASE}/track/{asin}")

    if resp.status_code != 200:
        raise RuntimeError(f"API returned {resp.status_code} — check your API_BASE config")

    data = resp.json()

    stream_url = (
        data.get("streamUrl")
        or data.get("stream_url")
        or data.get("url")
        or ""
    )
    decrypt_key = (
        data.get("decryptionKey")
        or data.get("decryption_key")
        or data.get("key")
        or ""
    )

    if not stream_url:
        raise RuntimeError("API didn't return a stream URL — ASIN might be invalid or unavailable")

    return {
        "asin":   asin,
        "title":  data.get("title") or asin,
        "artist": data.get("artist") or "Unknown Artist",
        "album":  data.get("album") or "",
        "stream": stream_url,
        "key":    decrypt_key,
    }


async def download_track(meta: dict) -> dict:
    asin = meta["asin"]
    enc_path = os.path.join(DOWNLOAD_DIR, f"{asin}_enc.m4a")

    async with httpx.AsyncClient(
        headers={"User-Agent": USER_AGENT},
        timeout=120,
        follow_redirects=True,
    ) as client:
        async with client.stream("GET", meta["stream"]) as resp:
            resp.raise_for_status()
            with open(enc_path, "wb") as f:
                async for chunk in resp.aiter_bytes(128 * 1024):
                    f.write(chunk)

    if not os.path.exists(enc_path) or os.path.getsize(enc_path) == 0:
        raise RuntimeError("downloaded file is empty — the stream URL might be dead")

    safe_name = re.sub(r'[\\/*?:"<>|]', "", f"{meta['artist']} - {meta['title']}")

    if not meta["key"]:
        out_path = os.path.join(DOWNLOAD_DIR, f"{safe_name}.m4a")
        os.rename(enc_path, out_path)
        return {**meta, "path": out_path, "codec": "m4a", "bits": None, "rate": None}

    loop = asyncio.get_running_loop()
    stream_info = await loop.run_in_executor(None, probe_audio, enc_path)

    codec = stream_info.get("codec_name", "m4a")
    ext = "flac" if codec == "flac" else ("m4a" if codec in ("aac", "alac") else codec)
    out_path = os.path.join(DOWNLOAD_DIR, f"{safe_name}.{ext}")

    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", "-loglevel", "error",
        "-decryption_key", meta["key"].strip(),
        "-i", enc_path,
        "-c", "copy",
        "-y", out_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()

    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg decryption failed: {stderr.decode()}")

    if not os.path.exists(out_path) or os.path.getsize(out_path) == 0:
        raise RuntimeError("output file is empty after decryption — key might be wrong")

    try:
        os.remove(enc_path)
    except Exception:
        pass

    return {
        **meta,
        "path":  out_path,
        "codec": codec,
        "bits":  stream_info.get("bits_per_raw_sample"),
        "rate":  stream_info.get("sample_rate"),
    }


def cleanup(*paths):
    for p in paths:
        if p and os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass


def user_tag(user) -> str:
    return f"@{user.username}" if user.username else f"<code>{user.id}</code>"


async def log_new_user(bot: Client, user) -> None:
    if not config.LOG_CHANNEL:
        return

    name = user.first_name + (f" {user.last_name}" if user.last_name else "")
    username = f"@{user.username}" if user.username else "<i>None</i>"

    text = (
        "<blockquote>"
        "🆕 <b>New User</b>\n\n"
        f"<b>Name     :</b>  <b>{name}</b>\n"
        f"<b>ID       :</b>  <code>{user.id}</code>\n"
        f"<b>Username :</b>  {username}"
        "</blockquote>"
    )

    photos = []
    try:
        async for photo in bot.get_chat_photos(user.id, limit=1):
            photos.append(photo)
    except Exception:
        pass

    try:
        if photos:
            await bot.send_photo(
                chat_id=config.LOG_CHANNEL,
                photo=photos[0].file_id,
                caption=text,
                parse_mode=ParseMode.HTML,
            )
        else:
            await bot.send_message(
                chat_id=config.LOG_CHANNEL,
                text=text,
                parse_mode=ParseMode.HTML,
            )
    except Exception as e:
        print(f"[log] couldn't send new-user log: {e}")


async def log_download(bot: Client, user, track: dict, file_id: str = None) -> None:
    if not config.LOG_CHANNEL:
        return

    tag = user_tag(user)
    name = user.first_name + (f" {user.last_name}" if user.last_name else "")
    fmt = "FLAC 24bit / 192kHz" if track["codec"] == "flac" else track["codec"].upper()

    text = (
        "<blockquote>"
        "🎵 <b>Track Downloaded</b>\n\n"
        f"<b>User     :</b>  <b>{name}</b>  ({tag})\n"
        f"<b>ID       :</b>  <code>{user.id}</code>\n\n"
        f"<b>Track    :</b>  <i>{track['title']}</i>\n"
        f"<b>Artist   :</b>  <i>{track['artist']}</i>"
        + (f"\n<b>Album    :</b>  <i>{track['album']}</i>" if track["album"] else "")
        + f"\n<b>Format   :</b>  <i>{fmt}</i>"
        "</blockquote>"
    )

    try:
        await bot.send_audio(
            chat_id=config.LOG_CHANNEL,
            audio=file_id or track["path"],
            caption=text,
            title=track["title"],
            performer=track["artist"],
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        print(f"[log] couldn't send download log: {e}")


async def cmd_start(bot: Client, msg: Message):
    user = msg.from_user

    try:
        if await mongodb.is_new_user(user.id):
            await mongodb.add_user(
                user_id=user.id,
                first_name=user.first_name,
                username=user.username,
                dc_id=user.dc_id,
            )
            await log_new_user(bot, user)
    except Exception as e:
        print(f"[db] new-user check failed: {e}")

    await msg.reply_text(
        "<blockquote>\n"
        "<b>Hey 👋</b>\n"
        "<b>Send me an Amazon Music track link and I'll download it for you.</b>\n\n"
        "<i>Just paste the link below.</i>\n"
        "</blockquote>",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Dev", url=config.DEV_URL, style=ButtonStyle.PRIMARY),
            InlineKeyboardButton("Credits", callback_data="credits", style=ButtonStyle.PRIMARY),
        ]]),
    )


async def cb_credits(_, cb: CallbackQuery):
    await cb.answer()
    await cb.message.reply_text(
        "<blockquote>\n"
        "<b>Credits</b>\n\n"
        "<i>This bot was built by</i> <b>Nick</b> <i>and</i> <b>Abhi (tenka)</b>.\n\n"
        "<i>Nick did most of the heavy lifting — if it helps you, just give credit. That's all.</i>\n"
        "</blockquote>",
        parse_mode=ParseMode.HTML,
    )


async def cb_dismiss(_, cb: CallbackQuery):
    await cb.answer()
    try:
        await cb.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass


async def handle_message(bot: Client, msg: Message):
    text = msg.text.strip()

    if not is_amazon_url(text):
        await msg.reply_text("that doesn't look like an amazon music link.")
        return

    if "/search/" in text or "/api/" in text:
        await msg.reply_text("send a direct track link, not a search or api url.")
        return

    status = await msg.reply_text("downloading...")

    try:
        asin = extract_asin(text)
        meta = await fetch_track_meta(asin)
        track = await download_track(meta)

        await status.edit_text("uploading...")
        await asyncio.sleep(1.5)

        fmt = "FLAC 24bit / 192kHz" if track["codec"] == "flac" else track["codec"].upper()
        caption = (
            f"<b>{track['title']}</b>\n"
            f"{track['artist']}"
            + (f" — {track['album']}" if track["album"] else "")
            + f"\n{fmt}"
        )

        sent = await msg.reply_audio(
            audio=track["path"],
            caption=caption,
            title=track["title"],
            performer=track["artist"],
            parse_mode=ParseMode.HTML,
        )

        await status.delete()

        file_id = sent.audio.file_id if sent and sent.audio else None
        await log_download(bot, msg.from_user, track, file_id)

        cleanup(track["path"])

    except Exception as e:
        await status.edit_text(
            f"something went wrong\n\n<code>{e}</code>",
            parse_mode=ParseMode.HTML,
        )


# ── entry point ───────────────────────────────────────────────────────────────

async def main():
    bot = Client(
        "amzn_bot",
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        bot_token=config.BOT_TOKEN,
    )

    # filters.private ensures the bot only responds in DMs , and if u want to work in the other places just remove the filters.private thats all
    bot.add_handler(MessageHandler(cmd_start, filters.command("start") & filters.private))
    bot.add_handler(CallbackQueryHandler(cb_credits, filters.regex("^credits$")))
    bot.add_handler(CallbackQueryHandler(cb_dismiss, filters.regex("^dismiss$")))
    bot.add_handler(MessageHandler(handle_message, filters.text & filters.private & ~filters.command(["start"])))

    await mongodb.connect()
    await bot.start()
    print("[bot] running — waiting for messages...")
    await idle()
    await bot.stop()
    await mongodb.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
