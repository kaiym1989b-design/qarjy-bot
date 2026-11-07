from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           KeyboardButton, ReplyKeyboardMarkup)

BTN_BALANCE = "📊 Баланс"
BTN_OBLIGATIONS = "📅 Міндетті төлемдер"
BTN_SETTINGS = "⚙️ Баптаулар"
BTN_HELP = "❓ Көмек"


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_BALANCE), KeyboardButton(text=BTN_OBLIGATIONS)],
            [KeyboardButton(text=BTN_SETTINGS), KeyboardButton(text=BTN_HELP)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Мысалы: 5000 такси",
    )


def inline(rows: list[list[tuple[str, str]]]) -> InlineKeyboardMarkup:
    """[[(мәтін, callback_data), ...], ...] -> InlineKeyboardMarkup"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t, callback_data=d) for t, d in row] for row in rows
    ])
