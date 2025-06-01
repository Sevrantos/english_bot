from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.fsm.student import Support
from bot.keyboards.inline_keyboard import cancel_kb
from bot.utils.config import ADMIN_IDS

router = Router()


@router.callback_query(F.data == "support")
async def send_bug(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Support.send)
    await state.update_data(message_id=callback.message.message_id)

    await callback.message.edit_text(
        "Опишіть проблему, з якою ви зіткнулися. "
        "Наші адміністратори розглянуть її якнайшвидше.",
        reply_markup=cancel_kb,
    )
    await callback.message.pin()


@router.message(Support.send)
async def forvard_bag(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await bot.edit_message_text(
        text="✅ Ваше повідомлення успішно надіслано адміністраторам.\n"
        "Дякуємо за зворотній зв'язок!",
        chat_id=message.from_user.id,
        message_id=data.get("message_id"),
        reply_markup=None,
    )
    await state.clear()

    for admin in ADMIN_IDS:
        try:
            await bot.forward_message(
                chat_id=admin,
                from_chat_id=message.from_user.id,
                message_id=message.message_id,
            )
        except:
            pass
