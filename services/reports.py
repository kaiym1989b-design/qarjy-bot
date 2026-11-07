"""Баланс, күнделікті дайджест және төлем ескертулерінің мәтіндері."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from html import escape

from db import repo
from services.finance import (MONTHS_KK, amount_needed, days_left_in_month,
                              format_amount, format_date_kk, month_bounds,
                              next_due_date)


@dataclass
class MonthStats:
    income: Decimal = Decimal(0)
    expense: Decimal = Decimal(0)
    by_category: list[tuple[str, Decimal]] = field(default_factory=list)  # тек шығыс
    obligations: list = field(default_factory=list)

    @property
    def balance(self) -> Decimal:
        return self.income - self.expense

    @property
    def obligations_total(self) -> Decimal:
        return sum((Decimal(o["amount"]) for o in self.obligations), Decimal(0))

    @property
    def needed(self) -> Decimal:
        return amount_needed(self.obligations_total, self.income)


async def load_month_stats(user_id, now: datetime) -> MonthStats:
    start, end = month_bounds(now)
    rows = await repo.month_summary(user_id, start, end)
    stats = MonthStats(obligations=await repo.list_obligations(user_id))
    cats: dict[str, Decimal] = {}
    for r in rows:
        if r["type"] == "income":
            stats.income += r["total"]
        else:
            stats.expense += r["total"]
            cats[r["category"]] = cats.get(r["category"], Decimal(0)) + r["total"]
    stats.by_category = sorted(cats.items(), key=lambda kv: kv[1], reverse=True)
    return stats


def _needed_lines(stats: MonthStats, today: date) -> list[str]:
    if not stats.obligations:
        return ["📌 Міндетті төлем қосылмаған — /obligations"]
    lines = [f"📌 Міндетті төлемдер: <b>{format_amount(stats.obligations_total)}</b> "
             f"({len(stats.obligations)} дана)"]
    if stats.needed > 0:
        days = days_left_in_month(today)
        per_day = (stats.needed / days).quantize(Decimal("1"))
        lines.append(f"🎯 Тағы табу керек: <b>{format_amount(stats.needed)}</b>")
        lines.append(f"   ≈ күніне {format_amount(per_day)} ({days} күн қалды)")
    else:
        extra = stats.income - stats.obligations_total
        lines.append(f"✅ Міндетті төлемдер кірісіңмен жабылды! Артығы: {format_amount(extra)}")
    return lines


def render_balance(stats: MonthStats, now: datetime) -> str:
    lines = [f"📊 <b>{MONTHS_KK[now.month - 1]} {now.year}</b>", ""]
    if stats.income == 0 and stats.expense == 0:
        lines.append("Бұл айда әзірге жазба жоқ. Мысалы, <code>5000 такси</code> деп жазып көр.")
    else:
        lines += [
            f"💰 Кіріс: <b>{format_amount(stats.income)}</b>",
            f"💸 Шығыс: <b>{format_amount(stats.expense)}</b>",
            f"⚖️ Баланс: <b>{format_amount(stats.balance)}</b>",
        ]
        if stats.by_category:
            lines += ["", "<b>Шығыс категориялары:</b>"]
            for name, total in stats.by_category:
                pct = round(total / stats.expense * 100) if stats.expense else 0
                lines.append(f"• {escape(name)} — {format_amount(total)} ({pct}%)")
    lines.append("")
    lines += _needed_lines(stats, now.date())
    return "\n".join(lines)


def render_digest(name: str | None, stats: MonthStats, now: datetime) -> str:
    today = now.date()
    hello = f"Сәлем, {escape(name)}!" if name else "Сәлем!"
    lines = [
        f"☀️ {hello} Күнделікті қаржы шолуы",
        f"📅 {format_date_kk(today)} · айдың соңына {days_left_in_month(today)} күн",
        "",
        f"💰 Осы айда тапқаның: <b>{format_amount(stats.income)}</b>",
        f"💸 Осы айдағы шығыс: <b>{format_amount(stats.expense)}</b>",
    ]
    lines += _needed_lines(stats, today)
    return "\n".join(lines)


def obligation_reminder_texts(obligations, today: date) -> list[str]:
    out = []
    for ob in obligations:
        due = next_due_date(ob["day_of_month"], today)
        delta = (due - today).days
        if delta not in (ob["remind_days_before"] or []):
            continue
        what = f"<b>{escape(ob['title'])}</b> — {format_amount(ob['amount'])}"
        if delta == 0:
            out.append(f"🔔 Бүгін төлем күні: {what}")
        else:
            out.append(f"⏰ {delta} күннен кейін ({format_date_kk(due)}) төлем: {what}")
    return out
