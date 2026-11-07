"""APScheduler: күнделікті дайджест, төлем ескертулері, апталық кеңес."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config import TZ, WEEKLY_TIP_DAY, WEEKLY_TIP_HOUR
from db import repo
from services.reports import (load_month_stats, obligation_reminder_texts,
                              render_digest)
from services.tips import tip_for_week

log = logging.getLogger(__name__)


async def safe_send(bot: Bot, chat_id: int, text: str) -> bool:
    """Жіберу. Қолданушы ботты бұғаттаса — құламаймыз, тек логқа жазамыз."""
    for _ in range(2):
        try:
            await bot.send_message(chat_id, text)
            return True
        except TelegramRetryAfter as e:  # Telegram «күте тұр» десе
            await asyncio.sleep(e.retry_after + 1)
        except TelegramForbiddenError:
            log.info("Қолданушы %s ботты бұғаттаған", chat_id)
            return False
        except Exception:
            log.exception("%s-ге жіберу сәтсіз", chat_id)
            return False
    return False


async def hourly_tick(bot: Bot, now: datetime | None = None) -> None:
    """Әр сағат басында: осы сағатты таңдаған қолданушыларға шолу + ескерту."""
    now = now or datetime.now(TZ)
    users = await repo.users_by_hour(now.hour)
    log.info("%s:00 — %d қолданушыға шолу", now.hour, len(users))
    for user in users:
        try:
            stats = await load_month_stats(user["id"], now)
            await safe_send(bot, user["telegram_id"], render_digest(user["name"], stats, now))
            for text in obligation_reminder_texts(stats.obligations, now.date()):
                await safe_send(bot, user["telegram_id"], text)
        except Exception:
            log.exception("Шолу қатесі (user=%s)", user["id"])
        await asyncio.sleep(0.05)  # Telegram лимитінен аспау үшін


async def weekly_tip(bot: Bot) -> None:
    text = tip_for_week(datetime.now(TZ).date())
    for user in await repo.all_users():
        await safe_send(bot, user["telegram_id"], text)
        await asyncio.sleep(0.05)


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=TZ)
    common = dict(args=[bot], coalesce=True, max_instances=1, misfire_grace_time=900)
    scheduler.add_job(hourly_tick, CronTrigger(minute=0, timezone=TZ), id="hourly", **common)
    scheduler.add_job(weekly_tip,
                      CronTrigger(day_of_week=WEEKLY_TIP_DAY, hour=WEEKLY_TIP_HOUR,
                                  minute=5, timezone=TZ),
                      id="weekly_tip", **common)
    return scheduler
