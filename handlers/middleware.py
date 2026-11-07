"""Әр хабарламада қолданушыны DB-да тіркеп (жоқ болса), хэндлерге `user` ретінде береді."""
from aiogram import BaseMiddleware

from db import repo


class UserMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        tg_user = data.get("event_from_user")
        if tg_user is not None and not tg_user.is_bot:
            data["user"] = await repo.ensure_user(tg_user.id, tg_user.full_name)
        return await handler(event, data)
