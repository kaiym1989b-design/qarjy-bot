"""Бот құламасын: кез келген қатені ұстап, қолданушыға қазақша түсіндіреміз."""
import logging

from aiogram.types import ErrorEvent

log = logging.getLogger(__name__)

ERROR_TEXT = ("⚠️ Кешіріңіз, бір қате шықты. Сәлден соң қайталап көріңіз.\n"
              "Қайталана берсе, /start басып көріңіз.")


async def on_error(event: ErrorEvent) -> bool:
    log.exception("Өңделмеген қате: %s", event.exception, exc_info=event.exception)
    update = event.update
    try:
        if update.callback_query:
            await update.callback_query.answer("⚠️ Қате шықты", show_alert=False)
            if update.callback_query.message:
                await update.callback_query.message.answer(ERROR_TEXT)
        elif update.message:
            await update.message.answer(ERROR_TEXT)
    except Exception:  # қате туралы хабарлама да жіберілмесе — тек логқа
        log.exception("Қате хабарламасын жіберу мүмкін болмады")
    return True
