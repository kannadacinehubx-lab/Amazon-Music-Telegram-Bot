<div align="center">

# 🎵 Amazon Music Bot

A Telegram bot that downloads Amazon Music tracks and sends them directly to your chat — supports AAC, ALAC, and FLAC (24-bit / 192kHz).

[![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python)](https://www.python.org/)
[![Kurigram](https://img.shields.io/badge/Framework-Kurigram-green?style=flat-square)](https://github.com/KurimuzonAkuma/kurigram)
[![MongoDB](https://img.shields.io/badge/Database-MongoDB-47A248?style=flat-square&logo=mongodb)](https://www.mongodb.com/)
[![Docker](https://img.shields.io/badge/Deploy-Docker-2496ED?style=flat-square&logo=docker)](https://www.docker.com/)

</div>

---

## ⚠️ Disclaimer

This is an **unofficial**, **educational** project. It is not affiliated with, endorsed by, or connected to Amazon or Amazon Music in any way. Use at your own risk and make sure you're complying with [Amazon's Terms of Service](https://www.amazon.com/gp/help/customer/display.html?nodeId=508088).

---

## 🔑 API Requirement

You need to buy API access from Amazon before this bot will do anything.

👉 [Amazon Music Developer Program](https://developer.amazon.com/docs/music/get_started_program-overview.html#amazon-music-developer)

Once you have access, set the base URL as `API_BASE` in your environment variables.

---

## What it does

Send the bot any Amazon Music track link and it downloads the track and sends it back to you as an audio file. It handles AAC, ALAC, and FLAC depending on what the API returns. If the track has a decryption key, ffmpeg takes care of that automatically.

It also logs new users and downloads to a private Telegram channel if you set one up, and keeps track of unique users in MongoDB.

---

## Project structure

```
├── amazon_music_bot.py   # bot logic
├── config.py             # environment variables
├── mongodb.py            
├── requirements.txt
├── Dockerfile
├── Procfile              # Heroku / Koyeb
├── heroku.yml            # Heroku Docker deployment
├── railway.toml          # Railway
├── render.yaml           # Render
├── nixpacks.toml         # Railway nixpacks / Koyeb fallback
├── runtime.txt           # Python version for Heroku
└── .env.example
```

---

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `API_ID` | ✅ | Telegram App ID from [my.telegram.org](https://my.telegram.org) |
| `API_HASH` | ✅ | Telegram App Hash from [my.telegram.org](https://my.telegram.org) |
| `BOT_TOKEN` | ✅ | Bot token from [@BotFather](https://t.me/BotFather) |
| `API_BASE` | ✅ | Your Amazon Music API base URL |
| `MONGO_URI` | ✅ | MongoDB connection string |
| `DB_NAME` | ❌ | Database name (default: `amzn_music_bot`) |
| `LOG_CHANNEL` | ❌ | Numeric ID of your log channel (default: `0` = disabled) |

---

## Deployment

This bot needs ffmpeg, so Docker is the cleanest option across all platforms.

### VPS / Local

```bash
git clone https://github.com/LastPerson07/Amazon-Music-Telegram-Bot.git
cd Amazon-Music-Telegram-Bot
cp .env.example .env
# fill in .env
docker build -t amzn-bot .
docker run --env-file .env amzn-bot
```

Or without Docker (requires ffmpeg installed on the system):

```bash
pip install -r requirements.txt
# export your env vars, then:
python amazon_music_bot.py
```

### Railway

1. Fork the repo
2. Create a new project on [Railway](https://railway.app) from your fork
3. Add all environment variables in the Railway dashboard
4. It'll pick up the `Dockerfile` via `railway.toml` and deploy automatically

### Render

1. Fork the repo
2. Create a new **Background Worker** on [Render](https://render.com)
3. Point it at your fork — Render will use `render.yaml`
4. Fill in the environment variables and deploy

### Heroku

Heroku uses `heroku.yml` to build from Docker (needed for ffmpeg):

```bash
heroku login
heroku create your-app-name
heroku stack:set container -a your-app-name
heroku config:set API_ID=... API_HASH=... BOT_TOKEN=... API_BASE=... MONGO_URI=...
git push heroku main
heroku ps:scale worker=1 -a your-app-name
```

### Koyeb

1. Create a new app on [Koyeb](https://koyeb.com)
2. Connect your GitHub repo
3. Koyeb will auto-detect the `Dockerfile`
4. Set environment variables in the Koyeb dashboard and deploy

---

## Usage

1. Start the bot with `/start`
2. Paste an Amazon Music track link, e.g.:
   ```
   https://music.amazon.in/albums/B0XXXXXXXX?trackAsin=B0YYYYYYYY
   ```
3. The bot downloads the track and sends it back as an audio file

Only direct track links work. Search URLs and API URLs are rejected.

---

## A few things to keep in mind

- The bot completely depends on your `API_BASE` endpoint — if the API is down or your key expires, nothing will work
- Track availability varies by region due to Amazon's licensing
- Keep your `.env` file out of version control — add it to `.gitignore`
- The `LOG_CHANNEL` should be a private channel only you can access

---

## Credits

Built by **Nick** and **Abhi (tenka)**.Dev-LastPerson07 Nick did most of the work on this — if it's useful to you, just give credit where it's due.
