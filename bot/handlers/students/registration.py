from aiogram import Bot, F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.fsm.student import Register
from bot.keyboards.inline_keyboard import use_full_name_kb
from bot.keyboards.keyboard import menu_kb
from bot.services.database.repositories.students import StudentRepository

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, db):
    student_repo = StudentRepository(db)
    if await student_repo.get_student(message.from_user.id):
        await message.answer("Так, я тут", reply_markup=menu_kb)
        return

    await state.set_state(Register.name)

    text = f"""
🔹 Програмуй майбутнє вже зараз!

Привіт! 🚀 Щоб почати навчання, зареєструйся:
👉 Введи своє ім’я в чаті
або
⬇ Натисни кнопку, щоб використати ім’я з Telegram ({message.from_user.full_name}).
"""
    send_message: Message = await message.answer(
        text=text, reply_markup=use_full_name_kb
    )

    await state.update_data(message_id=send_message.message_id)


@router.callback_query(Register.name, F.data == "use_tg_name")
async def cb_register_name(callback: CallbackQuery, state: FSMContext, db):
    student_repo = StudentRepository(db)

    await student_repo.add_student(
        callback.from_user.id, callback.from_user.full_name, callback.from_user.username
    )

    text = f"""
✅ {callback.from_user.full_name}, вітаємо у світі програмування!
🚀 Ти зареєстрований і готовий до навчання.
"""
    await callback.message.edit_text(text=text, reply_markup=None)
    await callback.message.answer(text="🔹 Почнемо?", reply_markup=menu_kb)

    await state.clear()


@router.message(Register.name)
async def register_name(message: Message, state: FSMContext, bot: Bot, db):
    student_repo = StudentRepository(db)

    await student_repo.add_student(
        message.from_user.id, message.text, message.from_user.username
    )

    text = f"""
✅ {message.text}, вітаємо у світі програмування!
🚀 Ти зареєстрований і готовий до навчання.
"""
    data = await state.get_data()
    await bot.delete_message(chat_id=message.chat.id, message_id=data.get("message_id"))
    await message.answer(text, reply_markup=menu_kb)

    await state.clear()
