"""Баптаулар — бәрі .env файлынан (немесе Railway Variables-тан) оқылады."""
import os
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
TZ = ZoneInfo(os.getenv("BOT_TIMEZONE", "Asia/Almaty"))
WEEKLY_TIP_DAY = os.getenv("WEEKLY_TIP_DAY", "sun")   # кеңес күні
WEEKLY_TIP_HOUR = int(os.getenv("WEEKLY_TIP_HOUR", "19"))


def validate() -> None:
    missing = [k for k, v in {"BOT_TOKEN": BOT_TOKEN, "DATABASE_URL": DATABASE_URL}.items() if not v]
    if missing:
        raise SystemExit(
            f"❌ Мына айнымалылар жоқ: {', '.join(missing)}. "
            ".env файлын толтырыңыз (.env.example үлгісін қараңыз).")
