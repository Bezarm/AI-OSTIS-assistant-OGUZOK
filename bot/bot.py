from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, Filter
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
import asyncio
from config import TOKEN
from kb_operations import Operator, Connector
import asyncio

bot = Bot(token=TOKEN)
dp = Dispatcher()
op = Operator()
conn = Connector()

@dp.message(Command('start'))
async def start(message: types.Message):
    op.add_user(message.from_user.id)
    await message.answer("1234")

@dp.message()
async def handle(message: types.Message):
    await message.answer(op.handle_message(message.from_user.id, message.from_user.full_name, message.text))

async def main():
    await dp.start_polling(bot)

if __name__=="__main__":
    conn.safe_connect('ws://localhost:8090')
    asyncio.run(main())