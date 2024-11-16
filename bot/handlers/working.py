import asyncio
import os

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from bot.utils.parser import TelegramBot
from bot.keyboards.inline_keyboard import create_inline_kb


router = Router()


class ChooseSession(StatesGroup):
    session_choose = State()
    chat_or_group = State()
    name = State()
    choose_work = State()
    hours = State()


@router.message(CommandStart())
async def command_start(message: Message, state: FSMContext):
    await state.clear()
    session_files = [f for f in os.listdir('.') if f.endswith('.session')]
    await message.answer('Выберите сессию, через которую хотите работать.', reply_markup=create_inline_kb(1, *session_files))
    await state.set_state(ChooseSession.session_choose)


@router.callback_query(F.data, ChooseSession.session_choose)
async def get_phone_number(callback: CallbackQuery, state: FSMContext):
    bot = TelegramBot(callback.data)
    await bot.start()
    await state.update_data(bot = bot)
    await callback.message.answer('Успешная авторизация. Выберите что хотите парсить?', reply_markup=create_inline_kb(1, 'Канал', 'Чат', 'Смешанный режим'))
    await state.set_state(ChooseSession.chat_or_group)

@router.callback_query(F.data, ChooseSession.chat_or_group)
async def chat_or_group(callback: CallbackQuery, state: FSMContext):
    if callback.data == 'Канал':
        await callback.message.answer('Введите название канала')
        await state.update_data(channel = 1)
        await state.update_data(chat = 0)
        await state.set_state(ChooseSession.name)
    elif callback.data == 'Чат':
        await callback.message.answer('Введите название чата')
        await state.update_data(chat = 1)
        await state.update_data(channel = 0)
        await state.set_state(ChooseSession.name)

@router.message(F.text, ChooseSession.name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name = message.text)
    data = await state.get_data()
    if data['channel'] == 1 and data['chat'] == 0:
        await message.answer('С телеграмм канала можно спарсить юзеров из комментариев за какое-то количество часов, либо же за все время\nРекомендовано парсить за некоторое время, так как для этого потребуется намного меньше времени.'
                             ,reply_markup=create_inline_kb(1, 'За все время', 'За некоторое время'))
    if data['chat'] == 1 and data['channel'] == 0:
        await message.answer('С чата можно спарсить либо всех участников, либо тех кто писал сообщения за n-срок, либо тех кто ставил реакции на какие то сообщения за n-ый срок',
                             reply_markup=create_inline_kb(1,'Участники', 'По сообщениям', 'По реакциям'))
    await state.set_state(ChooseSession.choose_work)

@router.callback_query(F.data, ChooseSession.choose_work)
async def choosing(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if callback.data == 'Участники':
        task = asyncio.create_task(data['bot'].parse_chat_members(data['name']))
        await task
        try:
            await callback.message.bot.send_document(chat_id=callback.from_user.id, document=FSInputFile(task.result()), caption='Файл со всеми учатниками чата')
        except Exception:
            await callback.message.answer('ИНформации не нашлось')
        os.remove(task.result())
        await state.clear()
    if callback.data == 'За все время':
        task = asyncio.create_task(data['bot'].parse_users_from_comments(data['name']))
        await task
        try:
            await callback.message.bot.send_document(chat_id=callback.from_user.id, document=FSInputFile(task.result()), caption='Файл со всеми юзерами из комментариев')
        except Exception:
            await callback.message.answer('Информации не нашлось')
        os.remove(task.result())
        await state.clear()
    if callback.data in ['За некоторое время', 'По сообщениям', 'По реакциям']:
        await state.update_data(choosed_for_hours = callback.data)
        await callback.message.answer('Введите количество часов, за которое хотите осуществить парсинг')
        await state.set_state(ChooseSession.hours)

@router.message(F.text, ChooseSession.hours)
async def get_hours(message: Message, state: FSMContext):
    data = await state.get_data()
    if data['choosed_for_hours'] == 'За некоторое время':
        task = asyncio.create_task(data['bot'].parse_users_from_comments(data['name'], int(message.text)))
        await task
        try:
            await message.bot.send_document(chat_id=message.from_user.id, document=FSInputFile(task.result()), caption=f'Файл со всеми юзерами из комментариев за последние {message.text} часов(а)')
        except Exception:
            await message.answer('Информации не нашлось')
        os.remove(task.result())
        await state.clear()
    if data['choosed_for_hours'] == 'По сообщениям':
        task = asyncio.create_task(data['bot'].get_active_users(data['name'], int(message.text)))
        await task
        try:
            await message.bot.send_document(chat_id=message.from_user.id, document=FSInputFile(task.result()), caption=f'Файл со всеми юзерами, которые писали за последние {message.text} часов(а)')
        except Exception:
            await message.answer('Информации не нашлось')
        os.remove(task.result())
        await state.clear()
    if data['choosed_for_hours'] == 'По реакциям':
        task = asyncio.create_task(data['bot'].get_users_with_reactions(data['name'], int(message.text)))
        await task
        try:
            await message.bot.send_document(chat_id=message.from_user.id, document=FSInputFile(task.result()), caption=f'Файл со всеми юзерами, которые оставляли реакции за последние {message.text} часов(а)')
        except Exception:
            await message.answer('Информации не нашлось')
        os.remove(task.result())
        await state.clear()

