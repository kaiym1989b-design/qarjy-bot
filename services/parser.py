"""Мәтіннен қаржы транзакциясын тану.

Негізгі функция: parse_transaction("50к азық-түлік")
  -> {"type": "expense", "amount": Decimal("50000.00"),
      "category": "Азық-түлік", "note": "азық-түлік"}
Тани алмаса None қайтарады.
"""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

# ---------------------------------------------------------------------------
# 1. СОМА
# ---------------------------------------------------------------------------
AMOUNT_RE = re.compile(
    r"""
    (?:(?P<sign>\+)\s*)?            # сан алдындағы «+» — кіріс белгісі
    (?<![\w.,])                     # сан сөздің ортасынан басталмасын (мысалы «tele2»)
    (?P<num>
        \d{1,3}(?:[  .,]\d{3})+(?!\d)   # мыңдық бөлгішпен: 50 000 / 50.000 / 1,500,000
      | \d+(?:[.,]\d+)?                      # жай сан немесе бөлшек: 50000 / 1.5 / 1,5
    )
    (?:\s*(?P<mult>млн|mln|мың|мын|тыс|к|k)(?!\w))?   # қысқарту: 50к, 2 млн, 50 мың
    """,
    re.VERBOSE | re.IGNORECASE,
)

# Тек мыңдық бөлгіштен тұратын сан екенін тексеру (бөлгішті алып тастау үшін)
GROUPED_RE = re.compile(r"\d{1,3}(?:[  .,]\d{3})+")

MULTIPLIERS = {
    None: Decimal(1),
    "к": Decimal(1_000),
    "k": Decimal(1_000),
    "мың": Decimal(1_000),
    "мын": Decimal(1_000),
    "тыс": Decimal(1_000),
    "млн": Decimal(1_000_000),
    "mln": Decimal(1_000_000),
}

# Валюта сөздері — сома емес, жай ғана мәтіннен алынып тасталады
CURRENCY_RE = re.compile(r"(?<!\w)(?:тг|тенге|теңге|tg|kzt)(?!\w)|₸", re.IGNORECASE)

MAX_AMOUNT = Decimal("999999999999.99")  # numeric(14,2) шегі
CENT = Decimal("0.01")


def _normalize_number(raw: str) -> Decimal:
    """'50 000' / '50.000' / '1,5' сияқты жолды Decimal-ға айналдырады."""
    if GROUPED_RE.fullmatch(raw):
        # Мыңдық бөлгіш: бос орын, нүкте, үтірді алып тастаймыз
        return Decimal(re.sub(r"[  .,]", "", raw))
    # Бөлшек сан: үтірді нүктеге ауыстырамыз (1,5 -> 1.5)
    return Decimal(raw.replace(",", "."))


def extract_amount(text: str) -> tuple[Decimal, re.Match] | None:
    """Мәтіндегі бірінші соманы табады. (сома, regex сәйкестігі) немесе None."""
    for match in AMOUNT_RE.finditer(text):
        try:
            value = _normalize_number(match.group("num"))
        except InvalidOperation:
            continue
        mult = match.group("mult")
        value = (value * MULTIPLIERS[mult.lower() if mult else None]).quantize(CENT)
        if value <= 0 or value > MAX_AMOUNT:
            return None
        return value, match
    return None


# ---------------------------------------------------------------------------
# 2. КІРІС пе, ШЫҒЫС па
# ---------------------------------------------------------------------------
INCOME_WORDS = ["табыс", "кіріс", "жалақы", "зарплата", "аванс", "премия",
                "сатылым", "түсім", "аударым келді", "ақша келді"]


def _has_word(text: str, word: str, exact: bool = False) -> bool:
    """Сөз басынан сәйкес келе ме. exact=False болса жалғауларды да қабылдайды
    («такси» -> «таксиге»), exact=True болса тек тұтас сөз («су», бірақ «сусын» емес)."""
    pattern = r"(?<!\w)" + re.escape(word) + (r"(?!\w)" if exact else "")
    return re.search(pattern, text) is not None


# ---------------------------------------------------------------------------
# 3. КАТЕГОРИЯ  (атауы, сөз басы бойынша, тек тұтас сөз)
# ---------------------------------------------------------------------------
CATEGORIES: list[tuple[str, list[str], list[str]]] = [
    ("Азық-түлік",
     ["азық", "тамақ", "дүкен", "базар", "магазин", "продукт", "сүт", "small", "magnum"],
     ["нан"]),
    ("Көлік/Жанармай",
     ["жанармай", "бензин", "заправка", "такси", "автобус", "метро", "парковка",
      "жолақы", "yandex go", "indriver"],
     ["жол", "азс"]),
    ("Кафе/Мейрамхана",
     ["кафе", "ресторан", "мейрамхана", "кофе", "kfc", "dodo", "бургер", "асхана",
      "обед", "пицца", "шаурма"],
     []),
    ("Коммуналка",
     ["квартира", "пәтер", "жалдау", "аренда", "свет", "интернет", "коммунал",
      "кредит", "рассрочка", "несие"],
     ["ток", "су"]),
    ("Киім",
     ["киім", "аяқкиім", "кроссовка", "куртка", "zara", "lc waikiki"],
     []),
    ("Денсаулық",
     ["дәрі", "аптека", "дәрігер", "емхана", "стоматолог", "анализ"],
     []),
    ("Ойын-сауық",
     ["кино", "ойын", "steam", "подписка", "жазылым", "netflix", "spotify", "концерт"],
     []),
    ("Байланыс",
     ["байланыс", "актив", "activ", "beeline", "tele2", "altel", "номер"],
     []),
]

# «газ» екі мағыналы: көлікке (метан/пропан) немесе үйге (коммуналка)
GAS_TRANSPORT_HINTS = ["көлік", "машина", "авто", "заправка", "азс", "пропан", "метан"]

INCOME_CATEGORY = "Кіріс"
OTHER_CATEGORY = "Басқа"


def detect_category(text: str) -> str:
    low = text.lower()
    for name, prefixes, exact_words in CATEGORIES:
        if any(_has_word(low, w) for w in prefixes) or any(
            _has_word(low, w, exact=True) for w in exact_words
        ):
            return name
    if _has_word(low, "газ", exact=True):
        if any(_has_word(low, h) for h in GAS_TRANSPORT_HINTS):
            return "Көлік/Жанармай"
        return "Коммуналка"
    return OTHER_CATEGORY


def _clean_note(text: str) -> str:
    text = CURRENCY_RE.sub(" ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" -,.:;")


# ---------------------------------------------------------------------------
# НЕГІЗГІ ФУНКЦИЯ
# ---------------------------------------------------------------------------
def parse_transaction(text: str) -> dict | None:
    if not text or not text.strip():
        return None

    found = extract_amount(text)
    if found is None:
        return None
    amount, match = found

    # Соманы (және «+» таңбасын) мәтіннен алып тастаймыз — қалғаны note болады
    note = _clean_note(text[: match.start()] + " " + text[match.end():])

    low = text.lower()
    is_income = bool(match.group("sign")) or any(_has_word(low, w) for w in INCOME_WORDS)

    return {
        "type": "income" if is_income else "expense",
        "amount": amount,
        "category": INCOME_CATEGORY if is_income else detect_category(note),
        "note": note,
    }
