import os

# ── telegram credentials ─────────────────────────────────────────────────────
API_ID    = int(os.getenv("API_ID", "22876298"))
API_HASH  = os.getenv("API_HASH", "cda7be15fbe283b5b97e8fb8c4233e36")
BOT_TOKEN = os.getenv("BOT_TOKEN", "8819041526:AAHc_miDIuam2fjuJd_6DE_2TXZCNLBK4po")

# ── developer info ───────────────────────────────────────────────────────────
DEV_URL      = os.getenv("DEV_URL", "https://t.me/cantarella_wuwa")
DEV_USERNAME = os.getenv("DEV_USERNAME", "@cantarella_wuwa")

# ── amazon music api ─────────────────────────────────────────────────────────
# you need to purchase access from the amazon developer program , for third party api reach out to telegram = @cantarella_wuwa
# https://developer.amazon.com/docs/music/get_started_program-overview.html
API_BASE = os.getenv("API_BASE", "https://amzn.afkarxyz.qzz.io/api")

# ── log channel ──────────────────────────────────────────────────────────────
# set to your private channel's numeric id, e.g. -1001234567890
# leave as 0 to disable logging
LOG_CHANNEL = int(os.getenv("LOG_CHANNEL", "-1003797665459"))

# ── mongodb ──────────────────────────────────────────────────────────────────
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://Vishnuabhyantha_db:Baadshah@cluster0.fuxtgqk.mongodb.net/?appName=Cluster0")
DB_NAME   = os.getenv("DB_NAME", "Cluster0")
