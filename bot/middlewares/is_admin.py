from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery


class IsAdminMiddleware(BaseMiddleware):
    def __init__(self, admin_ids: list[int]):
        self.admin_ids = admin_ids
        super().__init__()

    async def __call__(self, handler, event, data):
        user_id = event.from_user.id

        if user_id and user_id not in self.admin_ids:
            await event.answer("You are not authorized to use this command.")
            return

        await handler(event, data)