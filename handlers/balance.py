from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from config import TZ
from handlers.keyboards import BTN_BALANCE
from services.reports import load_month_stats, render_balance

router = Router(name="balance")


@router.message(Command("balance"))
@router.message(F.text == BTN_BALANCE)
async def cmd_balance(message: Message, state: FSMContext, user) -> None:
    await state.clear()
    now = datetime.now(TZ)
    stats = await load_month_stats(user["id"], now)
    await message.answer(render_balance(stats, now))
