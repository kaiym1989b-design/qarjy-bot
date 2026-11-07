"""Баптаулар — бәрі .env файлынан (немесе Railway Variables-тан) оқылады."""
import os
from urllib.parse import quote
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

# Supabase «qarjy-bot» жобасының Session pooler мекенжайы (құпия емес).
DB_HOST = os.getenv("DB_HOST", "aws-1-eu-central-1.pooler.supabase.com")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres.rblmvtnnsulgyeiblnrp")
DB_NAME = os.getenv("DB_NAME", "postgres")


def _build_database_url() -> str:
    """DATABASE_URL берілсе — соны, әйтпесе DB_PASSWORD-тан жолды өзі құрады."""
    url = os.getenv("DATABASE_URL", "").strip()
    if url:
        return url
    password = os.getenv("DB_PASSWORD", "").strip()
    if not password:
        return ""
    # quote(): құпиясөздегі @ # / сияқты таңбалар жолды бұзбасын
    return (f"postgresql://{quote(DB_USER, safe='.')}:{quote(password, safe='')}"
            f"@{DB_HOST}:{DB_PORT}/{DB_NAME}")


DATABASE_URL = _build_database_url()
TZ = ZoneInfo(os.getenv("BOT_TIMEZONE", "Asia/Almaty"))
WEEKLY_TIP_DAY = os.getenv("WEEKLY_TIP_DAY", "sun")   # кеңес күні
WEEKLY_TIP_HOUR = int(os.getenv("WEEKLY_TIP_HOUR", "19"))


def validate() -> None:
    missing = [k for k, v in {"BOT_TOKEN": BOT_TOKEN,
                              "DB_PASSWORD (немесе DATABASE_URL)": DATABASE_URL}.items() if not v]
    if missing:
        raise SystemExit(
            f"❌ Мына айнымалылар жоқ: {', '.join(missing)}. "
            ".env файлын толтырыңыз (.env.example үлгісін қараңыз).")
