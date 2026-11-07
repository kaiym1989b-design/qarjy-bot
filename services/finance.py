"""Таза есептеу функциялары (DB-сыз, тестке оңай)."""
from __future__ import annotations

import calendar
from datetime import date, datetime
from decimal import Decimal

MONTHS_KK = ["Қаңтар", "Ақпан", "Наурыз", "Сәуір", "Мамыр", "Маусым",
             "Шілде", "Тамыз", "Қыркүйек", "Қазан", "Қараша", "Желтоқсан"]
MONTHS_KK_GEN = ["қаңтар", "ақпан", "наурыз", "сәуір", "мамыр", "маусым",
                 "шілде", "тамыз", "қыркүйек", "қазан", "қараша", "желтоқсан"]


def month_bounds(now: datetime) -> tuple[datetime, datetime]:
    """Ағымдағы айдың басы (қоса) мен келесі айдың басы (қоспай)."""
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1)
    else:
        end = start.replace(month=start.month + 1)
    return start, end


def due_date_in_month(year: int, month: int, day: int) -> date:
    """31-і сияқты күн қысқа айда соңғы күнге ауысады (ақпан -> 28/29)."""
    last = calendar.monthrange(year, month)[1]
    return date(year, month, min(day, last))


def next_due_date(day_of_month: int, today: date) -> date:
    due = due_date_in_month(today.year, today.month, day_of_month)
    if due >= today:
        return due
    y, m = (today.year + 1, 1) if today.month == 12 else (today.year, today.month + 1)
    return due_date_in_month(y, m, day_of_month)


def days_left_in_month(today: date) -> int:
    """Бүгінді қоса алғанда айдың соңына дейінгі күн саны."""
    return calendar.monthrange(today.year, today.month)[1] - today.day + 1


def amount_needed(obligations_total: Decimal, income: Decimal) -> Decimal:
    """Міндетті төлемдерді жабу үшін осы айда тағы қанша табу керек."""
    return max(Decimal(0), Decimal(obligations_total) - Decimal(income))


def format_amount(value) -> str:
    v = Decimal(value).quantize(Decimal("0.01"))
    if v == v.to_integral_value():
        s = f"{int(v):,}"
    else:
        s = f"{v:,.2f}"
    return s.replace(",", " ") + " ₸"


def format_date_kk(d: date) -> str:
    return f"{d.day} {MONTHS_KK_GEN[d.month - 1]}"
