"""Еркін мәтінмен жылдам жазу: «50000 азық-түлік», «+200000 жалақы»."""
import logging
from html import escape
from uuid import UUID

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, Message

from db import repo
from handlers.keyboards import inline
from services.finance import format_amount
from services.parser import OTHER_CATEGORY, parse_transaction

log = logging.getLogger(__name__)
router = Router(name="transactions")

NOT_UNDERSTOOD = ("Түсінбедім 🤔\nМысалы: <code>50000 азық-түлік</code> немесе "
                  "<code>+200000 жалақы</code>\n\nКөмек: /help")


@router.message(StateFilter(None), F.text, ~F.text.startswith("/"))
async def quick_entry(message: Message, user) -> None:
    parsed = parse_transaction(message.text)
    if parsed is None:
        await message.answer(NOT_UNDERSTOOD)
        return

    tx_id = await repo.add_transaction(user["id"], parsed["type"], parsed["amount"],
                                       parsed["category"], parsed["note"])
    if parsed["category"] == OTHER_CATEGORY:
        # Кейін парсерге жаңа кілт сөздер қосу үшін логқа жазамыз
        log.info("UNCATEGORIZED: %r", parsed["note"])

    icon, label = ("💰", "Кіріс") if parsed["type"] == "income" else ("💸", "Шығыс")
    text = (f"✅ {label} жазылды: <b>{format_amount(parsed['amount'])}</b>\n"
            f"{icon} {escape(parsed['category'])}")
    if parsed["note"]:
        text += f"\n📝 {escape(parsed['note'])}"
    await message.answer(text, reply_markup=inline([[("↩️ Болдырмау", f"tx:undo:{tx_id}")]]))


@router.callback_query(F.data.startswith("tx:undo:"))
async def undo(cb: CallbackQuery, user) -> None:
    try:
        tx_id = UUID(cb.data.split(":", 2)[2])
    except ValueError:
        await cb.answer("Қате батырма", show_alert=True)
        return
    if await repo.delete_transaction(user["id"], tx_id):
        await cb.message.edit_text(cb.message.html_text + "\n\n<i>↩️ Болдырылмады — өшірілді</i>")
        await cb.answer("Өшірілді")
    else:
        await cb.message.edit_reply_markup(reply_markup=None)
        await cb.answer("Бұл жазба бұрын өшірілген", show_alert=True)


@router.message(StateFilter(None))
async def non_text(message: Message) -> None:
    if message.text:  # «/» басталған, бірақ белгісіз команда
        await message.answer("Мұндай команда жоқ. Тізімі: /help")
    else:
        await message.answer("Мен тек мәтінді түсінемін. Мысалы: <code>3500 такси</code>")
