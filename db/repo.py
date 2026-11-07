"""Барлық SQL сұраулары осында (бәрі async)."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from db.pool import get_pool


# ---------------- users ----------------
async def ensure_user(telegram_id: int, name: str | None):
    pool = get_pool()
    row = await pool.fetchrow("select * from users where telegram_id = $1", telegram_id)
    if row is not None:
        if name and row["name"] != name:
            row = await pool.fetchrow(
                "update users set name = $2 where id = $1 returning *", row["id"], name)
        return row
    return await pool.fetchrow(
        """insert into users (telegram_id, name) values ($1, $2)
           on conflict (telegram_id) do update set name = excluded.name
           returning *""",
        telegram_id, name)


async def set_reminder_hour(user_id: UUID, hour: int) -> None:
    await get_pool().execute("update users set reminder_hour = $2 where id = $1", user_id, hour)


async def users_by_hour(hour: int):
    return await get_pool().fetch("select * from users where reminder_hour = $1", hour)


async def all_users():
    return await get_pool().fetch("select * from users")


# ---------------- transactions ----------------
async def add_transaction(user_id: UUID, type_: str, amount: Decimal,
                          category: str, note: str) -> UUID:
    return await get_pool().fetchval(
        """insert into transactions (user_id, type, amount, category, note)
           values ($1, $2, $3, $4, $5) returning id""",
        user_id, type_, amount, category, note)


async def delete_transaction(user_id: UUID, tx_id: UUID) -> bool:
    res = await get_pool().execute(
        "delete from transactions where id = $1 and user_id = $2", tx_id, user_id)
    return res.endswith(" 1")


async def month_summary(user_id: UUID, start: datetime, end: datetime):
    return await get_pool().fetch(
        """select type, category, sum(amount) as total, count(*) as n
           from transactions
           where user_id = $1 and created_at >= $2 and created_at < $3
           group by type, category""",
        user_id, start, end)


# ---------------- obligations ----------------
async def list_obligations(user_id: UUID):
    return await get_pool().fetch(
        """select * from obligations where user_id = $1 and active
           order by day_of_month, title""", user_id)


async def get_obligation(user_id: UUID, ob_id: UUID):
    return await get_pool().fetchrow(
        "select * from obligations where id = $1 and user_id = $2 and active", ob_id, user_id)


async def add_obligation(user_id: UUID, title: str, amount: Decimal,
                         day_of_month: int, remind_days: list[int]) -> UUID:
    return await get_pool().fetchval(
        """insert into obligations (user_id, title, amount, day_of_month, remind_days_before)
           values ($1, $2, $3, $4, $5) returning id""",
        user_id, title, amount, day_of_month, remind_days)


# Тек осы бағандарды өзгертуге болады (SQL injection-нан қорғаныс)
_EDITABLE = {"title": "title", "amount": "amount",
             "day": "day_of_month", "remind": "remind_days_before"}


async def update_obligation(user_id: UUID, ob_id: UUID, field: str, value) -> bool:
    column = _EDITABLE[field]
    res = await get_pool().execute(
        f"update obligations set {column} = $3 where id = $1 and user_id = $2 and active",
        ob_id, user_id, value)
    return res.endswith(" 1")


async def delete_obligation(user_id: UUID, ob_id: UUID) -> bool:
    res = await get_pool().execute(
        "delete from obligations where id = $1 and user_id = $2", ob_id, user_id)
    return res.endswith(" 1")
