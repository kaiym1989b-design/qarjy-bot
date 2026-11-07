"""/obligations — ай сайынғы міндетті төлемдерді қосу / өңдеу / өшіру."""
from html import escape
from uuid import UUID

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from db import repo
from handlers.keyboards import BTN_OBLIGATIONS, inline
from services.finance import format_amount
from services.validators import (REMIND_PRESETS, InputError, describe_remind_days,
                                 parse_amount, parse_day, parse_remind_days,
                                 parse_title)

router = Router(name="obligations")


class AddOb(StatesGroup):
    title = State()
    amount = State()
    day = State()
    remind = State()


class EditOb(StatesGroup):
    value = State()


FIELD_PROMPTS = {
    "title": "Жаңа атауын жазыңыз:",
    "amount": "Жаңа соманы жазыңыз (мысалы <code>150000</code> немесе <code>150к</code>):",
    "day": "Айдың нешесінде төлейсіз? (1–31):",
    "remind": "Неше күн бұрын ескертейін? Таңдаңыз немесе жазыңыз (мысалы <code>5,1,0</code>):",
}
FIELD_PARSERS = {"title": parse_title, "amount": parse_amount,
                 "day": parse_day, "remind": parse_remind_days}


# ---------------- көмекші функциялар ----------------
def remind_kb():
    return inline([[(label, f"ob:rd:{key}")] for key, label in REMIND_PRESETS.items()])


def ob_card(ob) -> str:
    return (f"📌 <b>{escape(ob['title'])}</b>\n"
            f"Сомасы: <b>{format_amount(ob['amount'])}</b>\n"
            f"Төлем күні: әр айдың <b>{ob['day_of_month']}</b>-і\n"
            f"Ескерту: {describe_remind_days(ob['remind_days_before'])}")


def ob_kb(ob_id):
    return inline([
        [("✏️ Атауы", f"ob:edit:{ob_id}:title"), ("✏️ Сомасы", f"ob:edit:{ob_id}:amount")],
        [("✏️ Күні", f"ob:edit:{ob_id}:day"), ("✏️ Ескерту", f"ob:edit:{ob_id}:remind")],
        [("🗑 Өшіру", f"ob:del:{ob_id}")],
        [("⬅️ Тізімге", "ob:list")],
    ])


async def list_view(user_id):
    obs = await repo.list_obligations(user_id)
    if not obs:
        text = ("📅 <b>Міндетті төлемдер</b>\n\nӘзірге ештеңе жоқ.\n"
                "Квартира, кредит, интернет сияқты ай сайынғы төлемдерді қос — "
                "мен оларды уақытында еске салып отырамын.")
    else:
        total = sum(o["amount"] for o in obs)
        text = (f"📅 <b>Міндетті төлемдер</b> ({len(obs)})\n"
                f"Айына барлығы: <b>{format_amount(total)}</b>\n\nӨңдеу үшін таңдаңыз 👇")
    rows = [[(f"{o['title']} · {format_amount(o['amount'])} · {o['day_of_month']}-і",
              f"ob:view:{o['id']}")] for o in obs]
    rows.append([("➕ Жаңа төлем қосу", "ob:add")])
    return text, inline(rows)


def _uuid(s: str) -> UUID | None:
    try:
        return UUID(s)
    except ValueError:
        return None


# ---------------- тізім ----------------
@router.message(Command("obligations"))
@router.message(F.text == BTN_OBLIGATIONS)
async def cmd_obligations(message: Message, state: FSMContext, user) -> None:
    await state.clear()
    text, kb = await list_view(user["id"])
    await message.answer(text, reply_markup=kb)


@router.callback_query(F.data == "ob:list")
async def cb_list(cb: CallbackQuery, state: FSMContext, user) -> None:
    await state.clear()
    text, kb = await list_view(user["id"])
    await cb.message.edit_text(text, reply_markup=kb)
    await cb.answer()


@router.callback_query(F.data.startswith("ob:view:"))
async def cb_view(cb: CallbackQuery, user) -> None:
    ob_id = _uuid(cb.data.split(":", 2)[2])
    ob = await repo.get_obligation(user["id"], ob_id) if ob_id else None
    if ob is None:
        await cb.answer("Төлем табылмады", show_alert=True)
        return
    await cb.message.edit_text(ob_card(ob), reply_markup=ob_kb(ob["id"]))
    await cb.answer()


# ---------------- қосу: атауы → сомасы → күні → ескерту ----------------
@router.callback_query(F.data == "ob:add")
async def cb_add(cb: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AddOb.title)
    await cb.message.answer("1/4 · Төлемнің атауы қандай? (мысалы: <code>Квартира</code>)\n"
                            "Тоқтату: /cancel")
    await cb.answer()


@router.message(AddOb.title, F.text)
async def add_title(message: Message, state: FSMContext) -> None:
    try:
        title = parse_title(message.text)
    except InputError as e:
        await message.answer(str(e))
        return
    await state.update_data(title=title)
    await state.set_state(AddOb.amount)
    await message.answer("2/4 · Сомасы қанша? (мысалы <code>150000</code> немесе <code>150к</code>)")


@router.message(AddOb.amount, F.text)
async def add_amount(message: Message, state: FSMContext) -> None:
    try:
        amount = parse_amount(message.text)
    except InputError as e:
        await message.answer(str(e))
        return
    await state.update_data(amount=str(amount))
    await state.set_state(AddOb.day)
    await message.answer("3/4 · Айдың нешесінде төлейсіз? (1–31)\n"
                         "<i>31 десеңіз, қысқа айларда соңғы күні ескертемін.</i>")


@router.message(AddOb.day, F.text)
async def add_day(message: Message, state: FSMContext) -> None:
    try:
        day = parse_day(message.text)
    except InputError as e:
        await message.answer(str(e))
        return
    await state.update_data(day=day)
    await state.set_state(AddOb.remind)
    await message.answer("4/4 · " + FIELD_PROMPTS["remind"], reply_markup=remind_kb())


async def _finish_add(target: Message, state: FSMContext, user, days: list[int]) -> None:
    from decimal import Decimal
    data = await state.get_data()
    await state.clear()
    await repo.add_obligation(user["id"], data["title"], Decimal(data["amount"]),
                              data["day"], days)
    await target.answer(
        f"✅ Қосылды: <b>{escape(data['title'])}</b> — {format_amount(Decimal(data['amount']))}, "
        f"әр айдың {data['day']}-і.\nЕскерту: {describe_remind_days(days)}")
    text, kb = await list_view(user["id"])
    await target.answer(text, reply_markup=kb)


@router.message(AddOb.remind, F.text)
async def add_remind_text(message: Message, state: FSMContext, user) -> None:
    try:
        days = parse_remind_days(message.text)
    except InputError as e:
        await message.answer(str(e))
        return
    await _finish_add(message, state, user, days)


@router.callback_query(AddOb.remind, F.data.startswith("ob:rd:"))
async def add_remind_btn(cb: CallbackQuery, state: FSMContext, user) -> None:
    days = parse_remind_days(cb.data.split(":", 2)[2])
    await cb.message.edit_reply_markup(reply_markup=None)
    await cb.answer()
    await _finish_add(cb.message, state, user, days)


# ---------------- өңдеу ----------------
@router.callback_query(F.data.startswith("ob:edit:"))
async def cb_edit(cb: CallbackQuery, state: FSMContext, user) -> None:
    _, _, raw_id, field = cb.data.split(":", 3)
    ob_id = _uuid(raw_id)
    if field not in FIELD_PARSERS or not ob_id or not await repo.get_obligation(user["id"], ob_id):
        await cb.answer("Төлем табылмады", show_alert=True)
        return
    await state.set_state(EditOb.value)
    await state.update_data(ob_id=str(ob_id), field=field)
    await cb.message.answer(FIELD_PROMPTS[field] + "\nТоқтату: /cancel",
                            reply_markup=remind_kb() if field == "remind" else None)
    await cb.answer()


async def _apply_edit(target: Message, state: FSMContext, user, raw_value: str) -> None:
    data = await state.get_data()
    field, ob_id = data["field"], UUID(data["ob_id"])
    try:
        value = FIELD_PARSERS[field](raw_value)
    except InputError as e:
        await target.answer(str(e))
        return
    await state.clear()
    if not await repo.update_obligation(user["id"], ob_id, field, value):
        await target.answer("Төлем табылмады (өшірілген болуы мүмкін).")
        return
    ob = await repo.get_obligation(user["id"], ob_id)
    await target.answer("✅ Сақталды\n\n" + ob_card(ob), reply_markup=ob_kb(ob_id))


@router.message(EditOb.value, F.text)
async def edit_value(message: Message, state: FSMContext, user) -> None:
    await _apply_edit(message, state, user, message.text)


@router.callback_query(EditOb.value, F.data.startswith("ob:rd:"))
async def edit_remind_btn(cb: CallbackQuery, state: FSMContext, user) -> None:
    await cb.message.edit_reply_markup(reply_markup=None)
    await cb.answer()
    await _apply_edit(cb.message, state, user, cb.data.split(":", 2)[2])


@router.callback_query(F.data.startswith("ob:rd:"))
async def stale_remind_btn(cb: CallbackQuery) -> None:
    await cb.answer("Бұл батырма ескірген. /obligations қайта ашыңыз.", show_alert=True)


# ---------------- өшіру ----------------
@router.callback_query(F.data.startswith("ob:del:"))
async def cb_delete(cb: CallbackQuery, user) -> None:
    ob_id = _uuid(cb.data.split(":", 2)[2])
    ob = await repo.get_obligation(user["id"], ob_id) if ob_id else None
    if ob is None:
        await cb.answer("Төлем табылмады", show_alert=True)
        return
    await cb.message.edit_text(
        f"«{escape(ob['title'])}» төлемін өшіреміз бе?",
        reply_markup=inline([[("🗑 Иә, өшір", f"ob:delok:{ob_id}"),
                              ("Жоқ", f"ob:view:{ob_id}")]]))
    await cb.answer()


@router.callback_query(F.data.startswith("ob:delok:"))
async def cb_delete_ok(cb: CallbackQuery, user) -> None:
    ob_id = _uuid(cb.data.split(":", 2)[2])
    ok = bool(ob_id) and await repo.delete_obligation(user["id"], ob_id)
    text, kb = await list_view(user["id"])
    await cb.message.edit_text(("🗑 Өшірілді.\n\n" if ok else "") + text, reply_markup=kb)
    await cb.answer("Өшірілді" if ok else "Табылмады")
