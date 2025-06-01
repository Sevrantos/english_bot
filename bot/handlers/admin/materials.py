from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.types.input_file import InputFile
from aiogram.types.input_media_document import InputMediaDocument
from aiogram.types.input_media_photo import InputMediaPhoto

from bot.fsm.admin import AddMaterials
from bot.keyboards.inline_keyboard import LessonCB, ListComands, cancel_kb
from bot.services.database.repositories.lessons import LessonRepository

router = Router()


@router.callback_query(LessonCB.filter(F.cmd == ListComands.edit.value))
async def admin_add_material(
    callback: CallbackQuery, callback_data: LessonCB, state: FSMContext, db
):
    lesson_repo = LessonRepository(db)

    await state.set_state(AddMaterials.add)
    await state.update_data(message_id=callback.message.message_id)
    await state.update_data(lesson_id=callback_data.lesson_id)

    await lesson_repo.delete_materials(callback_data.lesson_id)

    await callback.message.edit_text(
        "Відправте матеріали для уроку, вони оновлять існуючі матеріали",
        reply_markup=cancel_kb,
    )
    await callback.message.pin()


@router.message(AddMaterials.add, F.document)
async def add_materials_document(message: Message, state: FSMContext, db):
    lesson_repo = LessonRepository(db)
    data = await state.get_data()

    await lesson_repo.add_material(
        lesson_id=data.get("lesson_id"),
        file_id=message.document.file_id,
        file_type="document",
    )

    await message.reply("Документ додано")


@router.message(AddMaterials.add, F.photo)
async def add_materials_photo(message: Message, state: FSMContext, db):
    lesson_repo = LessonRepository(db)
    data = await state.get_data()

    await lesson_repo.add_material(
        lesson_id=data.get("lesson_id"),
        file_id=message.photo[-1].file_id,
        file_type="photo",
    )

    await message.reply("Photo додано")


@router.message(AddMaterials.add, F.audio)
async def add_materials_audio(message: Message, state: FSMContext, db):
    lesson_repo = LessonRepository(db)
    data = await state.get_data()

    await lesson_repo.add_material(
        lesson_id=data.get("lesson_id"),
        file_id=message.audio.file_id,
        file_type="audio",
    )

    await message.reply("Audio додано")


@router.message(AddMaterials.add, F.video)
async def add_materials_video(message: Message, state: FSMContext, db):
    lesson_repo = LessonRepository(db)
    data = await state.get_data()

    await lesson_repo.add_material(
        lesson_id=data.get("lesson_id"),
        file_id=message.video.file_id,
        file_type="video",
    )

    await message.reply("Video додано")
