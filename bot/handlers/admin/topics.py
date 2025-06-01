import json
import os
from io import BytesIO

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.types.input_file import BufferedInputFile
from pydantic import ValidationError

from bot.fsm.admin import AddQuiz, AddTopic
from bot.keyboards.inline_keyboard import (
    ClassCB,
    ListComands,
    TopicCB,
    cancel_kb,
    lessons_kb_generator,
    topics_kb_generator,
)
from bot.services.database.models import QuizData
from bot.services.database.repositories.lessons import LessonRepository
from bot.services.database.repositories.quizzes import QuizRepository
from bot.services.database.repositories.topics import TopicRepository

router = Router()


# open_topic
@router.callback_query(
    TopicCB.filter(F.cmd == ListComands.open.value), TopicCB.filter(F.admin == True)
)
async def open_admin_topic(callback: CallbackQuery, callback_data: TopicCB, db):
    lessson_repo = LessonRepository(db)

    lessons = await lessson_repo.get_lessons_by_topic(callback_data.topic_id)

    await callback.message.edit_text(
        f"Відкриття уроки для адміністратора",
        reply_markup=await lessons_kb_generator(
            lessons=lessons,
            class_number=callback_data.class_number,
            topic_id=callback_data.topic_id,
            cmd=ListComands.open,
            admin=True,
        ),
    )


# add_topic
@router.callback_query(TopicCB.filter((F.cmd == ListComands.add.value)))
async def add_topic(callback: CallbackQuery, callback_data: TopicCB, state: FSMContext):
    await state.update_data(message_id=callback.message.message_id)
    await state.update_data(class_number=callback_data.class_number)
    await state.set_state(AddTopic.title)

    await callback.message.edit_text(
        f"Додавання теми у {callback_data.class_number} клас \nНадайте назву теми",
        reply_markup=cancel_kb,
    )
    await callback.message.pin()


@router.message(AddTopic.title)
async def receive_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(AddTopic.description)
    await message.answer("Додайте опис теми")


@router.message(AddTopic.description)
async def receive_description(message: Message, state: FSMContext, bot: Bot, db):
    topic_repo = TopicRepository(db)
    descrpiption = message.text
    data = await state.get_data()

    await topic_repo.add_topic(
        data.get("title"),
        description=descrpiption,
        class_number=data.get("class_number"),
    )
    await bot.edit_message_reply_markup(
        chat_id=message.from_user.id,
        message_id=data.get("message_id"),
        reply_markup=None,
    )
    await bot.unpin_all_chat_messages(chat_id=message.from_user.id)

    await message.answer("Додано тему")
    await state.clear()


# delete_topic
@router.callback_query(
    TopicCB.filter((F.cmd == ListComands.delete.value) & (F.topic_id == 0))
)
async def cmd_delete(callback: CallbackQuery, callback_data: TopicCB, db):
    topic_repo = TopicRepository(db)
    topics = await topic_repo.get_topics_by_class(callback_data.class_number)

    await callback.message.edit_text(
        f"Видалення тем з {callback_data.class_number} клас",
        reply_markup=await topics_kb_generator(
            topics=topics,
            class_number=callback_data.class_number,
            cmd=ListComands.delete,
            admin=True,
        ),
    )


@router.callback_query(
    TopicCB.filter((F.cmd == ListComands.cancel.value) & (F.topic_id == 0))
)
async def cmd_cancel(callback: CallbackQuery, callback_data: TopicCB, db):
    topic_repo = TopicRepository(db)
    topics = await topic_repo.get_topics_by_class(callback_data.class_number)

    await callback.message.edit_text(
        f"{callback_data.class_number} клас",
        reply_markup=await topics_kb_generator(
            topics=topics,
            class_number=callback_data.class_number,
            cmd=ListComands.open,
            admin=True,
        ),
    )


@router.callback_query(
    TopicCB.filter((F.cmd == ListComands.delete.value) & (F.topic_id != 0))
)
async def topic_delete(callback: CallbackQuery, callback_data: TopicCB, db):
    topic_repo = TopicRepository(db)
    await topic_repo.delete_topic(callback_data.topic_id)
    topics = await topic_repo.get_topics_by_class(callback_data.class_number)

    await callback.message.edit_reply_markup(
        reply_markup=await topics_kb_generator(
            topics=topics,
            class_number=callback_data.class_number,
            cmd=ListComands.delete,
            admin=True,
        )
    )


# add_quiz
@router.callback_query(TopicCB.filter(F.cmd == ListComands.add_quiz.value))
async def add_quiz(callback: CallbackQuery, callback_data: TopicCB, state: FSMContext):
    await state.set_state(AddQuiz.add)
    await state.update_data(message_id=callback.message.message_id)
    await state.update_data(topic_id=callback_data.topic_id)

    example_test = """{
    "questions": [
        {
            "question": "Який файл використовується для зберігання метаданих проекту в Python?",
            "options": [
                "setup.py",
                "pyproject.toml", 
                "requirements.txt",
                "metadata.json"
            ],
            "correct_answer": 1
        },
        {
            "question": "Для чого використовується віртуальне середовище в Python?",
            "options": [
                "Для прискорення виконання коду",
                "Для ізоляції залежностей проекту",
                "Для компіляції Python коду",
                "Для тестування коду"
            ],
            "correct_answer": 1
        }
    ]
    }"""

    await callback.message.edit_text(
        "Додавання модульний тесту до теми\n\n"
        "Завантажте JSON файл з тестом у такому форматі:\n"
        f"<pre>{example_test}</pre>",
        reply_markup=cancel_kb,
        parse_mode="HTML",
    )
    await callback.message.pin()


@router.message(AddQuiz.add, F.document)
async def receive_quiz(message: Message, state: FSMContext, bot: Bot, db):
    quiz_repo = QuizRepository(db)
    document = message.document

    if document.mime_type == "application/json" or document.file_name.endswith(".json"):
        file_data = BytesIO()
        await bot.download(document, destination=file_data)

        # try:
        json_data = file_data.getvalue().decode("utf-8")
        quiz_data = QuizData.model_validate_json(json_data)

        data = await state.get_data()

        await quiz_repo.add_quiz(topic_id=data.get("topic_id"), quiz_data=quiz_data)

        await message.reply(f"Успішно завантажено {len(quiz_data.questions)} питань!")

        await bot.edit_message_text(
            "Додано модульний тест",
            chat_id=message.from_user.id,
            message_id=data.get("message_id"),
            reply_markup=None,
        )
        await bot.unpin_all_chat_messages(chat_id=message.from_user.id)

        await state.clear()

        # except:
        #     await message.reply("The uploaded file contains invalid JSON.")
    else:
        await message.reply("Please upload a valid JSON file.")


# get_quiz
@router.callback_query(TopicCB.filter(F.cmd == ListComands.get_quiz.value))
async def get_quiz(callback: CallbackQuery, callback_data: TopicCB, db):
    quiz_repo = QuizRepository(db)
    quiz = await quiz_repo.get_quiz(callback_data.topic_id)

    if not quiz:
        await callback.answer()
        await callback.message.answer("Модульний тест відсутній")
        return

    # send it by file
    quiz_dict = quiz.model_dump()
    quiz_json = json.dumps(quiz_dict, indent=4)
    file_data = BytesIO(quiz_json.encode("utf-8"))
    input_file = BufferedInputFile(
        file_data.getvalue(), filename=f"quiz_{callback_data.topic_id}.json"
    )

    await callback.message.answer_document(
        document=input_file,
        caption="Модульний тест",
    )
    await callback.answer()
