from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.keyboards.inline_keyboard import (
    ClassCB,
    ListComands,
    class_kb_generator,
    topics_kb_generator,
)
from bot.services.database.repositories.topics import TopicRepository

router = Router()


@router.message(Command(commands=["admin"]))
async def show_admin_classes(message: Message):
    await message.answer(
        "Admin \n Виберіть клас",
        reply_markup=await class_kb_generator(1, 11, admin=True),
    )


@router.callback_query(F.data == "admin_classes")
async def cb_show_admin_classes(callback: CallbackQuery):
    await callback.message.edit_text(
        "Admin \n Виберіть клас",
        reply_markup=await class_kb_generator(1, 11, admin=True),
    )


@router.callback_query(ClassCB.filter(F.admin == True))
async def show_admin_topics(callback: CallbackQuery, callback_data: ClassCB, db):
    topic_repo = TopicRepository(db)

    topics = await topic_repo.get_topics_by_class(callback_data.class_number)

    await callback.message.edit_text(
        f"{callback_data.class_number} Клас",
        reply_markup=await topics_kb_generator(
            topics=topics,
            class_number=callback_data.class_number,
            cmd=ListComands.open,
            admin=True,
        ),
    )
