"""Міндетті төлем формасындағы енгізулерді тексеру."""
from __future__ import annotations

import re
from decimal import Decimal

from services.parser import extract_amount

REMIND_PRESETS = {
    "7,2,0": "7 және 2 күн бұрын + сол күні",
    "3,1,0": "3 және 1 күн бұрын + сол күні",
    "1,0": "1 күн бұрын + сол күні",
    "0": "Тек сол күні",
}


class InputError(ValueError):
    """Қолданушыға көрсетілетін қазақша қате мәтіні."""


def parse_title(text: str) -> str:
    title = re.sub(r"\s+", " ", (text or "")).strip()
    if not title:
        raise InputError("Атауын жазыңыз, мысалы: <code>Квартира</code>")
    if len(title) > 60:
        raise InputError("Атауы тым ұзын (60 таңбадан аспасын).")
    return title


def parse_amount(text: str) -> Decimal:
    found = extract_amount(text or "")
    if not found:
        raise InputError("Соманы түсінбедім. Мысалы: <code>150000</code> немесе <code>150к</code>")
    return found[0]


def parse_day(text: str) -> int:
    t = (text or "").strip()
    if not t.isdigit() or not 1 <= int(t) <= 31:
        raise InputError("Айдың күнін 1-ден 31-ге дейінгі санмен жазыңыз. Мысалы: <code>10</code>")
    return int(t)


def parse_remind_days(text: str) -> list[int]:
    parts = re.split(r"[\s,;]+", (text or "").strip())
    try:
        days = sorted({int(p) for p in parts if p}, reverse=True)
    except ValueError:
        raise InputError("Күндерді үтірмен жазыңыз. Мысалы: <code>7,2,0</code>") from None
    if not days or any(d < 0 or d > 28 for d in days) or len(days) > 5:
        raise InputError("0-ден 28-ге дейінгі 1–5 сан жазыңыз. Мысалы: <code>7,2,0</code>")
    return days


def describe_remind_days(days: list[int]) -> str:
    parts = ["сол күні" if d == 0 else f"{d} күн бұрын" for d in sorted(days, reverse=True)]
    return ", ".join(parts)
