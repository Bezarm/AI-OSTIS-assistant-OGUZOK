from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, Filter
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
import asyncio
from config import TOKEN
from kb_operations import Operator, Connector
from sc_kpm import ScKeynodes
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
    op.add_message(message.from_user.id, message.text)
    #await message.answer("1234")

def on_nika_reply(text):
    print(543)
    asyncio.run(send(text))

async def main():
    #op.subscribe_to_message(send)
    await dp.start_polling(bot)

if __name__=="__main__":
    conn.safe_connect('ws://localhost:8090')
    asyncio.run(main())