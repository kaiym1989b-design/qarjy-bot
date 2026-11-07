"""Қаржы боты — іске қосу нүктесі."""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

import config
from db.pool import apply_schema, close_pool, init_pool
from handlers import balance, obligations, settings, start, transactions
from handlers.errors import on_error
from handlers.middleware import UserMiddleware
from services.reminders import setup_scheduler

COMMANDS = [
    BotCommand(command="start", description="Бастау"),
    BotCommand(command="balance", description="Осы айдағы баланс"),
    BotCommand(command="obligations", description="Міндетті төлемдер"),
    BotCommand(command="settings", description="Ескерту сағаты"),
    BotCommand(command="help", description="Көмек"),
    BotCommand(command="cancel", description="Әрекетті тоқтату"),
]


async def main() -> None:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    config.validate()

    await init_pool(config.DATABASE_URL)
    await apply_schema()

    bot = Bot(config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    user_mw = UserMiddleware()
    dp.message.outer_middleware(user_mw)
    dp.callback_query.outer_middleware(user_mw)
    dp.errors.register(on_error)

    # Рет маңызды: еркін мәтін (transactions) ең соңында
    dp.include_routers(start.router, balance.router, settings.router,
                       obligations.router, transactions.router)

    scheduler = setup_scheduler(bot)
    try:
        await bot.set_my_commands(COMMANDS)
        await bot.delete_webhook(drop_pending_updates=False)
        scheduler.start()
        logging.info("Бот іске қосылды ✅")
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)
        await close_pool()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
