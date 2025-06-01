from itertools import groupby
from operator import attrgetter

from aiogram import F, Router
from aiogram.types import (
    CallbackQuery,
    InputMediaAudio,
    InputMediaDocument,
    InputMediaPhoto,
    InputMediaVideo,
)

from bot.keyboards.inline_keyboard import LessonCB, ListComands, lesson_kb_generator
from bot.services.database.repositories.lessons import LessonRepository

router = Router()


@router.callback_query(LessonCB.filter(F.cmd == ListComands.open.value))
async def open_lessons(callback: CallbackQuery, callback_data: LessonCB, db):
    lesson_repo = LessonRepository(db)

    lesson = await lesson_repo.get_lessson(callback_data.lesson_id)
    class_number = await lesson_repo.get_class_by_lesson(callback_data.lesson_id)

    text = f"""
📝 Урок: {lesson.title}
ℹ️ Опис: {lesson.description}

Використовуйте кнопки нижче для:
- Перегляду навчальних матеріалів
- Проходження тесту
- Повернення до списку уроків
    """

    await callback.message.edit_text(
        text,
        reply_markup=await lesson_kb_generator(
            lesson=lesson, class_number=class_number
        ),
    )


@router.callback_query(LessonCB.filter(F.cmd == ListComands.get_materials.value))
async def get_materials(callback: CallbackQuery, callback_data: LessonCB, db):
    lesson_repo = LessonRepository(db)
    materials = await lesson_repo.get_materials(callback_data.lesson_id)

    if not materials:
        await callback.message.answer(
            "На жаль, для цього уроку ще немає додаткових матеріалів. "
            "Але ви можете переглянути основний вміст уроку вище."
        )
        await callback.answer()
        return

    # Group materials by type
    materials.sort(key=attrgetter("type"))
    grouped_materials = groupby(materials, key=attrgetter("type"))

    for material_type, group in grouped_materials:  # Unpack tuple into type and group
        materials_list = list(group)

        if len(materials_list) == 1:
            # Send single material
            material = materials_list[0]
            if material.type == "document":
                await callback.message.answer_document(material.file_id)
            elif material.type == "photo":
                await callback.message.answer_photo(material.file_id)
            elif material.type == "audio":
                await callback.message.answer_audio(material.file_id)
            elif material.type == "video":
                await callback.message.answer_video(material.file_id)
        else:
            # Send media group
            media_group = []
            for material in materials_list:
                if material.type == "document":
                    media_group.append(InputMediaDocument(media=material.file_id))
                elif material.type == "photo":
                    media_group.append(InputMediaPhoto(media=material.file_id))
                elif material.type == "audio":
                    media_group.append(InputMediaAudio(media=material.file_id))
                elif material.type == "video":
                    media_group.append(InputMediaVideo(media=material.file_id))

            if media_group:
                await callback.message.answer_media_group(media_group)

    await callback.answer()
