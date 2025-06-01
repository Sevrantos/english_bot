from aiogram import F, Router
from aiogram.filters import Command
from aiogram.filters.state import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

router = Router()


@router.callback_query(F.data == "cancel", StateFilter("*"))
async def cb_cancel(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Операція скасована", reply_markup=None)
    await callback.message.unpin()
    await state.clear()


@router.message(Command(commands=["cancel"]), StateFilter("*"))
async def cancel(message: Message, state: FSMContext):
    await message.answer("Операція скасована")
    await state.clear()
