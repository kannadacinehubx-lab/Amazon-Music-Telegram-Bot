import os

# ── telegram credentials ─────────────────────────────────────────────────────
API_ID    = int(os.getenv("API_ID", "0"))
API_HASH  = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# ── developer info ───────────────────────────────────────────────────────────
DEV_URL      = os.getenv("DEV_URL", "https://t.me/cantarella_wuwa")
DEV_USERNAME = os.getenv("DEV_USERNAME", "@cantarella_wuwa")

# ── amazon music api ─────────────────────────────────────────────────────────
# you need to purchase access from the amazon developer program , for third party api reach out to telegram = @cantarella_wuwa
# https://developer.amazon.com/docs/music/get_started_program-overview.html
API_BASE = os.getenv("API_BASE", "")

# ── log channel ──────────────────────────────────────────────────────────────
# set to your private channel's numeric id, e.g. -1001234567890
# leave as 0 to disable logging
LOG_CHANNEL = int(os.getenv("LOG_CHANNEL", "0"))

# ── mongodb ──────────────────────────────────────────────────────────────────
MONGO_URI = os.getenv("MONGO_URI", "")
DB_NAME   = os.getenv("DB_NAME", "amzn_music_bot")
