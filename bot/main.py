import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from handlers import working

from aiogram.enums.parse_mode import ParseMode


bot = Bot(token="7834950694:AAFBr42AaxY_7wYyfdipuHpFxMo_kKpqru4", default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
dp.include_router(working.router)


async def start_bot():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(start_bot())

