from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, Filter
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from config import TOKEN

bot = Bot(token=TOKEN)
dp = Dispatcher()

