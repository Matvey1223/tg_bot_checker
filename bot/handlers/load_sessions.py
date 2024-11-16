from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

router = Router()

@router.message(Command('load_session'))
async def load_session_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer('Загрузите файл сессии.')


@router.message(F.document)
async def handle_document(message: Message):
    document = message.document

    file_path = f"{document.file_name}"

    file = await message.bot.get_file(document.file_id)
    await message.bot.download_file(file.file_path, destination=file_path)

    await message.answer(f"Файл '{document.file_name}' успешно сохранен")