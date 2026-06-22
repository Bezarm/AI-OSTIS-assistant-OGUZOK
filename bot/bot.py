from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, Filter
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
import asyncio
from config import TOKEN
from kb_operations import Operator, Connector
from cv_operations import Model
import logging

bot = Bot(token=TOKEN)
dp = Dispatcher()
conn = Connector()
conn.safe_connect('ws://localhost:8090')
op = Operator()
mdl = Model()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("logs.log"), logging.StreamHandler()])
logger = logging.getLogger()

@dp.message(Command('start'))
async def start(message: types.Message):
    op.add_user(message.from_user.id, message.from_user.full_name)
    await message.answer("👋 Привет! Я <b>OGUZOK</b> (<b>O</b>ntological <b>G</b>astronomic <b>Us</b>er-<b>o</b>riented <b>C</b>ompanion) — твой кулинарный помощник! 🍳\n\nНапиши \"Что ты умеешь\", чтобы узнать подробнее.", parse_mode='HTML')

@dp.message(F.photo)
async def handle(message: types.Message):
    photo = message.photo[-1]
    smes = await message.reply("🔬 Анализирую изображение...")
    file_bytes = await message.bot.download(photo)  # io.BytesIO
    print(1)
    result = mdl.analyze(file_bytes)
    await smes.edit_text(op.ingr_add(message.from_user.id, result), parse_mode='HTML')

@dp.message()
async def handle(message: types.Message):
    op.add_user(message.from_user.id, message.from_user.full_name)
    clasif, text, entities = op.handle_message(message.from_user.id, message.from_user.full_name, message.text)
    if clasif == 9:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🍳 Начать готовку", callback_data=f"recipe-{entities[0]}-1")]])
        await message.answer(text, reply_markup=keyboard, parse_mode='HTML')
    else:
        await message.answer(text, parse_mode='HTML')

@dp.callback_query(lambda query: query.data.startswith('recipe-'))
async def step(callback_query: types.CallbackQuery):
    q = callback_query.data.split('-')
    text, is_f, is_l = op.get_step(q[1], int(q[2]))
    if is_f:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="➡️ Далее", callback_data=f"recipe-{q[1]}-{int(q[2])+1}")]])
    elif is_l:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data=f"recipe-{q[1]}-{int(q[2])-1}")]])
    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data=f"recipe-{q[1]}-{int(q[2])-1}"), 
                                                        InlineKeyboardButton(text="➡️ Далее", callback_data=f"recipe-{q[1]}-{int(q[2])+1}")]])
    await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode='HTML')

async def main():
    await dp.start_polling(bot)

if __name__=="__main__":
    asyncio.run(main())