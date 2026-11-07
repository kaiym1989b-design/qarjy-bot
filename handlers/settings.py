from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from db import repo
from handlers.keyboards import BTN_SETTINGS, inline

router = Router(name="settings")


def hours_kb(current: int):
    hours = list(range(6, 24))
    rows = []
    for i in range(0, len(hours), 6):
        rows.append([(f"✅{h}" if h == current else f"{h}:00", f"set:hour:{h}")
                     for h in hours[i:i + 6]])
    return inline(rows)


def settings_text(hour: int) -> str:
    return (f"⚙️ <b>Баптаулар</b>\n\nКүнделікті шолу сағаты: <b>{hour}:00</b> (Алматы уақыты)\n\n"
            "Басқа сағатты таңда 👇")


@router.message(Command("settings"))
@router.message(F.text == BTN_SETTINGS)
async def cmd_settings(message: Message, state: FSMContext, user) -> None:
    await state.clear()
    hour = user["reminder_hour"]
    await message.answer(settings_text(hour), reply_markup=hours_kb(hour))


@router.callback_query(F.data.startswith("set:hour:"))
async def set_hour(cb: CallbackQuery, user) -> None:
    try:
        hour = int(cb.data.rsplit(":", 1)[1])
        assert 0 <= hour <= 23
    except (ValueError, AssertionError):
        await cb.answer("Қате сағат", show_alert=True)
        return
    await repo.set_reminder_hour(user["id"], hour)
    await cb.message.edit_text(settings_text(hour), reply_markup=hours_kb(hour))
    await cb.answer(f"Сақталды: күн сайын {hour}:00 ✅")
