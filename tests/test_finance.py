from datetime import date, datetime
from decimal import Decimal

import pytest

from services.finance import (amount_needed, days_left_in_month, format_amount,
                              month_bounds, next_due_date)
from services.reports import obligation_reminder_texts
from services.validators import InputError, parse_day, parse_remind_days


def test_next_due_date_same_month():
    assert next_due_date(10, date(2026, 11, 7)) == date(2026, 11, 10)


def test_next_due_date_next_month_and_year():
    assert next_due_date(5, date(2026, 12, 20)) == date(2027, 1, 5)


def test_next_due_date_clamps_short_month():
    assert next_due_date(31, date(2027, 2, 1)) == date(2027, 2, 28)


def test_days_left():
    assert days_left_in_month(date(2026, 11, 7)) == 24
    assert days_left_in_month(date(2026, 11, 30)) == 1


def test_month_bounds_december():
    start, end = month_bounds(datetime(2026, 12, 15, 10))
    assert start == datetime(2026, 12, 1) and end == datetime(2027, 1, 1)


def test_amount_needed():
    assert amount_needed(Decimal(300000), Decimal(100000)) == Decimal(200000)
    assert amount_needed(Decimal(100000), Decimal(300000)) == 0


def test_format_amount():
    assert format_amount(Decimal("1500000")) == "1 500 000 ₸"
    assert format_amount(Decimal("12.5")) == "12.50 ₸"


def test_reminders_fire_on_right_days():
    obs = [{"title": "Квартира", "amount": Decimal(150000), "day_of_month": 14,
            "remind_days_before": [7, 2, 0]}]
    assert len(obligation_reminder_texts(obs, date(2026, 11, 7))) == 1   # 7 күн қалды
    assert obligation_reminder_texts(obs, date(2026, 11, 8)) == []        # 6 күн — жоқ
    assert "Бүгін" in obligation_reminder_texts(obs, date(2026, 11, 14))[0]


def test_validators():
    assert parse_remind_days("7, 2 0") == [7, 2, 0]
    assert parse_day("31") == 31
    for bad in ["0", "32", "abc"]:
        with pytest.raises(InputError):
            parse_day(bad)
    with pytest.raises(InputError):
        parse_remind_days("40")
