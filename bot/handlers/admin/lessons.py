import json
from io import BytesIO

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.types.input_file import BufferedInputFile

from bot.fsm.admin import AddLesson
from bot.keyboards.inline_keyboard import (
    LessonCB,
    ListComands,
    admin_lesson_kb_generator,
    cancel_kb,
    lessons_kb_generator,
)
from bot.services.database.models import TestData
from bot.services.database.repositories.lessons import LessonRepository
from bot.services.database.repositories.tests import TestRepository
from bot.services.database.repositories.topics import TopicRepository

router = Router()


# open_lesson
@router.callback_query(
    LessonCB.filter(F.cmd == ListComands.open.value), LessonCB.filter(F.admin == True)
)
async def open_admin_lesson(callback: CallbackQuery, callback_data: LessonCB, db):
    repo = LessonRepository(db)
    lesson = await repo.get_lessson(callback_data.lesson_id)  # Assumes method exists
    class_number = await repo.get_class_by_lesson(callback_data.lesson_id)

    await callback.message.edit_text(
        f"Урок: {lesson.title}",
        reply_markup=await admin_lesson_kb_generator(lesson, class_number),
    )


# add_lesson
@router.callback_query(
    LessonCB.filter((F.cmd == ListComands.add.value) & (F.lesson_id == 0))
)
async def add_lesson(
    callback: CallbackQuery, callback_data: LessonCB, state: FSMContext
):
    await state.update_data(message_id=callback.message.message_id)
    await state.update_data(topic_id=callback_data.topic_id)
    await state.set_state(AddLesson.title)
    await callback.message.edit_text(
        f"Додавання уроку до теми \nВведіть назву уроку", reply_markup=cancel_kb
    )
    await callback.message.pin()


@router.message(AddLesson.title)
async def receive_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(AddLesson.description)
    await message.answer("Додайте опис уроку")


@router.message(AddLesson.description)
async def receive_description(message: Message, state: FSMContext, bot: Bot, db):
    lesson_repo = LessonRepository(db)
    data = await state.get_data()
    await lesson_repo.add_lesson(
        title=data.get("title"), description=message.text, topic_id=data.get("topic_id")
    )
    await bot.edit_message_reply_markup(
        chat_id=message.from_user.id,
        message_id=data.get("message_id"),
        reply_markup=None,
    )
    await bot.unpin_all_chat_messages(chat_id=message.from_user.id)

    await message.answer("Урок додано")
    await state.clear()


# delete_lesson
@router.callback_query(LessonCB.filter(F.cmd == ListComands.delete.value))
async def admin_delete_lesson(callback: CallbackQuery, callback_data: LessonCB, db):
    lesson_repo = LessonRepository(db)
    topic_repo = TopicRepository(db)
    await lesson_repo.delete_lesson(callback_data.lesson_id)  # Assumes method exists
    lessons = await lesson_repo.get_lessons_by_topic(callback_data.topic_id)
    topic = await topic_repo.get_topic(callback_data.topic_id)

    await callback.message.edit_text(
        f"Відкриття уроки для адміністратора",
        reply_markup=await lessons_kb_generator(
            lessons=lessons,
            class_number=topic.class_number,
            topic_id=callback_data.topic_id,
            cmd=ListComands.open,
            admin=True,
        ),
    )


# add_test
@router.callback_query(LessonCB.filter(F.cmd == ListComands.add_test.value))
async def add_test(callback: CallbackQuery, callback_data: LessonCB, state: FSMContext):
    await state.set_state(AddLesson.add_test)
    await state.update_data(message_id=callback.message.message_id)
    await state.update_data(lesson_id=callback_data.lesson_id)

    example_test = """{
    "questions": [
        {
            "question": "What is the main difference between 'print' and 'return' in Python?",
            "options": [
                "print displays output, return sends value back to the caller",
                "They are the same thing", 
                "return displays output, print sends value back to the caller",
                "Neither displays output"
            ],
            "correct_answer": 0
        },
        {
            "question": "Which data type is mutable in Python?",
            "options": [
                "string",
                "tuple", 
                "list",
                "integer"
            ],
            "correct_answer": 2
        }
    ]
}"""

    await callback.message.edit_text(
        "Додавання тесту до уроку\n\n"
        "Завантажте JSON файл з тестом у такому форматі:\n"
        f"<pre>{example_test}</pre>",
        reply_markup=cancel_kb,
        parse_mode="HTML",
    )
    await callback.message.pin()


@router.message(AddLesson.add_test, F.document)
async def receive_test(message: Message, state: FSMContext, bot: Bot, db):
    test_repo = TestRepository(db)
    lesson_repo = LessonRepository(db)
    document = message.document

    if document.mime_type == "application/json" or document.file_name.endswith(".json"):
        file_data = BytesIO()
        await bot.download(document, destination=file_data)

        json_data = file_data.getvalue().decode("utf-8")
        test_data = TestData.model_validate_json(json_data)

        data = await state.get_data()
        lesson_id = data.get("lesson_id")

        await test_repo.add_test(lesson_id=lesson_id, test_data=test_data)

        await message.reply(f"Успішно завантажено {len(test_data.questions)} питань!")

        await bot.edit_message_text(
            "Тест додано",
            chat_id=message.from_user.id,
            message_id=data.get("message_id"),
            reply_markup=None,
        )
        await bot.unpin_all_chat_messages(chat_id=message.from_user.id)

        # Get and display lesson after test is added
        lesson = await lesson_repo.get_lessson(lesson_id)
        class_number = await lesson_repo.get_class_by_lesson(lesson_id)
        await message.answer(
            f"Урок: {lesson.title}",
            reply_markup=await admin_lesson_kb_generator(lesson, class_number),
        )

        await state.clear()
    else:
        await message.reply("Please upload a valid JSON file.")


# get_test
@router.callback_query(
    LessonCB.filter(F.cmd == ListComands.get_test.value),
    LessonCB.filter(F.admin == True),
)
async def get_test(callback: CallbackQuery, callback_data: LessonCB, db):
    test_repo = TestRepository(db)
    test = await test_repo.get_test(callback_data.lesson_id)

    if not test:
        await callback.answer()
        await callback.answer("Тест відсутній", show_alert=True)
        return

    test_dict = test.model_dump()
    test_json = json.dumps(test_dict, indent=4)
    file_data = BytesIO(test_json.encode("utf-8"))
    input_file = BufferedInputFile(
        file_data.getvalue(), filename=f"test_{callback_data.lesson_id}.json"
    )

    await callback.message.answer_document(
        document=input_file,
        caption="Тест до уроку",
    )
    await callback.answer()
