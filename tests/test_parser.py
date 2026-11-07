from decimal import Decimal

import pytest

from services.parser import parse_transaction

CASES = [
    # мәтін,                    type,      сома,        категория
    ("50к азық-түлік",          "expense", "50000",     "Азық-түлік"),
    ("50000 азық-түлік",        "expense", "50000",     "Азық-түлік"),
    ("50 000 базар",            "expense", "50000",     "Азық-түлік"),
    ("50.000 дүкен",            "expense", "50000",     "Азық-түлік"),
    ("50,000 магазин",          "expense", "50000",     "Азық-түлік"),
    ("50 мың тамақ",            "expense", "50000",     "Азық-түлік"),
    ("50k нан",                 "expense", "50000",     "Азық-түлік"),
    ("1,5к нан",                "expense", "1500",      "Азық-түлік"),
    ("+200000 жалақы",          "income",  "200000",    "Кіріс"),
    ("+15 000 сатылым",         "income",  "15000",     "Кіріс"),
    ("аванс 100к",              "income",  "100000",    "Кіріс"),
    ("аударым келді 25000",     "income",  "25000",     "Кіріс"),
    ("такси 3500",              "expense", "3500",      "Көлік/Жанармай"),
    ("3500тг такси",            "expense", "3500",      "Көлік/Жанармай"),
    ("бензин 20 000 тенге",     "expense", "20000",     "Көлік/Жанармай"),
    ("заправка газ 8000",       "expense", "8000",      "Көлік/Жанармай"),
    ("1.5к кофе",               "expense", "1500",      "Кафе/Мейрамхана"),
    ("50 кофе",                 "expense", "50",        "Кафе/Мейрамхана"),
    ("kfc 4500",                "expense", "4500",      "Кафе/Мейрамхана"),
    ("квартира 150 000",        "expense", "150000",    "Коммуналка"),
    ("2млн аренда",             "expense", "2000000",   "Коммуналка"),
    ("2 млн кредит",            "expense", "2000000",   "Коммуналка"),
    ("2.5 млн рассрочка",       "expense", "2500000",   "Коммуналка"),
    ("газ 5000",                "expense", "5000",      "Коммуналка"),
    ("су 3000",                 "expense", "3000",      "Коммуналка"),
    ("zara 25000",              "expense", "25000",     "Киім"),
    ("5000 ₸ аптека",           "expense", "5000",      "Денсаулық"),
    ("steam 15к",               "expense", "15000",     "Ойын-сауық"),
    ("beeline 3000",            "expense", "3000",      "Байланыс"),
    ("tele2 5000",              "expense", "5000",      "Байланыс"),
    ("бірдеңе 777",             "expense", "777",       "Басқа"),
    ("сусын 400",               "expense", "400",       "Басқа"),  # «су» тұтас сөз емес
]


@pytest.mark.parametrize("text,type_,amount,category", CASES)
def test_parse(text, type_, amount, category):
    r = parse_transaction(text)
    assert r is not None, text
    assert r["type"] == type_
    assert r["amount"] == Decimal(amount)
    assert isinstance(r["amount"], Decimal)
    assert r["category"] == category


@pytest.mark.parametrize("text", ["", "   ", "сәлем", "такси", "0 нан", "тг"])
def test_not_understood(text):
    assert parse_transaction(text) is None


@pytest.mark.parametrize("text,note", [
    ("50к азық-түлік", "азық-түлік"),
    ("+200000 жалақы", "жалақы"),
    ("3500тг  такси   үйге", "такси үйге"),
    ("150000", ""),
    ("tele2 5000", "tele2"),
])
def test_note(text, note):
    assert parse_transaction(text)["note"] == note
