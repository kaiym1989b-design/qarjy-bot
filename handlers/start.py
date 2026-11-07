from html import escape

from aiogram import F, Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from handlers.keyboards import BTN_HELP, main_menu

router = Router(name="start")

HELP_TEXT = (
    "<b>Қалай жазу керек:</b>\n"
    "• <code>5000 такси</code> — шығыс\n"
    "• <code>50к азық-түлік</code> — 50 000 ₸ шығыс\n"
    "• <code>+200000 жалақы</code> — кіріс (+ белгісі немесе «жалақы», «аванс» сөздері)\n"
    "• <code>2 млн аренда</code>, <code>1.5к кофе</code> — бәрі түсінікті\n\n"
    "<b>Командалар:</b>\n"
    "/balance — осы айдағы кіріс, шығыс, баланс\n"
    "/obligations — ай сайынғы міндетті төлемдер\n"
    "/settings — күнделікті ескерту сағаты\n"
    "/cancel — басталған әрекетті тоқтату\n\n"
    "Әр күні белгілеген сағатта «тағы қанша табу керек» екенін айтып тұрамын, "
    "ал төлем күні жақындаса — ескертемін 🔔"
)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, user) -> None:
    await state.clear()
    name = escape(user["name"] or "досым")
    await message.answer(
        f"Сәлем, {name}! 👋\n\n"
        "Мен — қаржы көмекшіңмін. Кіріс-шығысыңды есептеймін, міндетті төлемдерді "
        "еске саламын және ай соңына дейін тағы қанша табу керек екенін көрсетемін.\n\n"
        "<b>Бастау өте оңай:</b> жай ғана жаз, мысалы <code>3500 такси</code> 🚕\n\n"
        "Алдымен /obligations арқылы квартира, кредит сияқты тұрақты төлемдеріңді қосып ал — "
        "сонда есеп нақты болады.",
        reply_markup=main_menu(),
    )


@router.message(Command("help"))
@router.message(F.text == BTN_HELP)
async def cmd_help(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(HELP_TEXT, reply_markup=main_menu())


@router.message(Command("cancel"), StateFilter("*"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    had_state = await state.get_state() is not None
    await state.clear()
    await message.answer("Тоқтатылды ✋" if had_state else "Тоқтататын әрекет жоқ.",
                         reply_markup=main_menu())
