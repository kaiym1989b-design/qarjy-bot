"""Postgres байланыс пулы (asyncpg)."""
from __future__ import annotations

import logging
from pathlib import Path

import asyncpg

log = logging.getLogger(__name__)
_pool: asyncpg.Pool | None = None
SCHEMA_FILE = Path(__file__).with_name("schema.sql")


async def init_pool(dsn: str) -> asyncpg.Pool:
    global _pool
    # statement_cache_size=0 — Supabase pooler (pgbouncer) үшін міндетті
    _pool = await asyncpg.create_pool(dsn, min_size=1, max_size=5,
                                      statement_cache_size=0, command_timeout=30)
    log.info("Дерекқорға қосылды")
    return _pool


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("DB пулы әлі ашылмаған")
    return _pool


async def apply_schema() -> None:
    """Кестелер жоқ болса құрады (бар болса ештеңе өзгертпейді).

    Бот шектеулі қолданушымен қосылса, кесте құруға құқығы болмайды —
    бұл қалыпты: кестелер Supabase-те алдын ала құрылған, жай жалғастырамыз.
    """
    try:
        await get_pool().execute(SCHEMA_FILE.read_text(encoding="utf-8"))
        log.info("Схема тексерілді")
    except asyncpg.InsufficientPrivilegeError:
        log.info("Схеманы өзгертуге құқық жоқ — кестелер бұрыннан бар деп есептейміз")
    # Кестелер шынымен қолжетімді ме — тексереміз (жоқ болса, бот бірден анық қате береді)
    await get_pool().fetchval("select count(*) from users")


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
