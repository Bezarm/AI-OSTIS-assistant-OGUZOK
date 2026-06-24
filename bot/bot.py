from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, Filter
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from aiohttp.web_request import Request
from aiohttp_jinja2 import setup, render_template
from jinja2 import FileSystemLoader
from pathlib import Path
import asyncio
from config import TOKEN, URL, SECRET_KEY, ADMIN
from kb_operations import Operator, Connector
from cv_operations import Model
from classifier import Keyworder
import logging

bot = Bot(token=TOKEN)
dp = Dispatcher()
conn = Connector()
conn.safe_connect('ws://localhost:8090')
op = Operator()
mdl = Model()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler(Path(__file__).parent / 'logs.log'), logging.StreamHandler()])
logger = logging.getLogger()

RECIPES_TO_VERIFY = []

@dp.message(Command('start'))
async def start(message: types.Message):
    op.add_user(message.from_user.id, message.from_user.full_name)
    keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Что ты умеешь?"), KeyboardButton(text="Мои ингредиенты")],[KeyboardButton(text="Что приготовить?"), KeyboardButton(text="Как приготовить драники")]], resize_keyboard=True)
    await message.answer("👋 Привет! Я <b>OGUZOK</b> (<b>O</b>ntological <b>G</b>astronomic <b>Us</b>er-<b>o</b>riented <b>C</b>ompanion) — твой кулинарный помощник! 🍳\n\nНапиши \"Что ты умеешь\", чтобы узнать подробнее.", parse_mode='HTML', reply_markup=keyboard)

@dp.message(F.photo)
async def handle(message: types.Message):
    photo = message.photo[-1]
    smes = await message.reply("🔬 Анализирую изображение...")
    file_bytes = await message.bot.download(photo)  # io.BytesIO
    result = mdl.analyze(file_bytes)
    await smes.edit_text(op.ingr_add(message.from_user.id, result), parse_mode='HTML')

@dp.message()
async def handle(message: types.Message):
    logger.info(f"{message.from_user.id}, {message.from_user.full_name}")
    op.add_user(message.from_user.id, message.from_user.full_name)
    clasif, text, entities = op.handle_message(message.from_user.id, message.from_user.full_name, message.text)
    logger.info(f"{message.text} ({clasif}, {text})")
    match clasif:
        case 8: 
            builder = ReplyKeyboardBuilder()
            for e in entities:
                builder.button(text=f'Рецепт "{e}"')
            builder.adjust(2)
            await message.answer(text, reply_markup=builder.as_markup(one_time_keyboard=True), parse_mode='HTML')
        case 9:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🍳 Начать готовку", callback_data=f"recipe-{entities[0]}-1")]])
            await message.answer(text, reply_markup=keyboard, parse_mode='HTML')
        case 5:
            keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Что приготовить?")]], resize_keyboard=True)
            await message.answer(text, reply_markup=keyboard, parse_mode='HTML')
        case _:
            keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Что у меня есть?")], [KeyboardButton(text="Что приготовить?")]], resize_keyboard=True)
            await message.answer(text, reply_markup=keyboard, parse_mode='HTML')

@dp.callback_query(lambda query: query.data.startswith('recipe-'))
async def step(callback_query: types.CallbackQuery):
    q = callback_query.data.split('-')
    text, is_f, is_l = op.get_step(q[1], int(q[2]))
    if is_f:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="➡️ Далее", callback_data=f"recipe-{q[1]}-{int(q[2])+1}")]])
    elif is_l:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data=f"recipe-{q[1]}-{int(q[2])-1}")], [InlineKeyboardButton(text="Завершить готовку", callback_data=f"finish-{q[1]}")]])
    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data=f"recipe-{q[1]}-{int(q[2])-1}"), 
                                                        InlineKeyboardButton(text="➡️ Далее", callback_data=f"recipe-{q[1]}-{int(q[2])+1}")]])
    await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode='HTML')

@dp.callback_query(lambda query: query.data.startswith('finish-'))
async def finish(callback_query: types.CallbackQuery):
    q = callback_query.data.split('-')
    if q[1] not in op.get_rec_pref(callback_query.from_user.id):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❤️ Блюдо понравилось", callback_data=f"liked-{q[1]}")], [InlineKeyboardButton(text="❌ Удалить все ингредиенты", callback_data="del")]])
    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Удалить все ингредиенты", callback_data="del")]])
    await callback_query.message.edit_text("🤗 Спасибо, что используете OGUZOK", reply_markup=keyboard, parse_mode='HTML')

@dp.callback_query(lambda query: query.data.startswith('liked-'))
async def liked(callback_query: types.CallbackQuery):
    q = callback_query.data.split('-')
    op.add_rec_pref(callback_query.from_user.id, callback_query.from_user.full_name, q[1])
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Удалить все ингредиенты", callback_data="del")]])
    await callback_query.message.edit_text("🤗 Спасибо, что используете OGUZOK\n Блюдо добавлено в любимое", reply_markup=keyboard, parse_mode='HTML')

@dp.callback_query(lambda query: query.data.startswith('del'))
async def delr(callback_query: types.CallbackQuery):
    await callback_query.message.edit_text(op.ingr_all_del(callback_query.from_user.id), parse_mode='HTML')


@dp.callback_query(lambda query: query.data.startswith('approve-'))
async def appr(callback_query: types.CallbackQuery):
    q = callback_query.data.split('-')
    op.add_recipe(RECIPES_TO_VERIFY[int(q[1])])
    await callback_query.message.edit_text("принято")

@dp.callback_query(lambda query: query.data.startswith('deny-'))
async def deny(callback_query: types.CallbackQuery):
    await callback_query.message.edit_text("отклонено")
    

async def on_startup(bot: Bot):
    await bot.set_webhook(f"{URL}/webhook",secret_token=SECRET_KEY)

async def on_shutdown(bot: Bot):
    await bot.delete_webhook()

async def add_recipe_get(request: Request):
    return render_template("recipe_form.html", request, {'success': False, 'ingrs': Keyworder().get_ingr_keys()})

async def add_recipe(request: Request):
    data = await request.post()
    sid = data.get('sid', '')
    name = data.get('name', '')
    time = data.get('time', '')
    portions = data.get('portions', '')
    difficulty = data.get('difficulty', '')
    calories = data.get('calories', '')
    
    ingredients = []
    i = 0
    while True:
        ingr_name = data.get(f'ingr_name_{i}')
        if ingr_name is None:
            break
        ingredients.append({
            'name': ingr_name,
            'amount': data.get(f'ingr_amount_{i}', ''),
            'unit': data.get(f'ingr_unit_{i}', 'грамм'),
        })
        i += 1

    steps = []
    i = 1
    while True:
        step_title = data.get(f'step_title_{i}')
        if step_title is None:
            break
        steps.append({
            'title': step_title,
            'description': data.get(f'step_desc_{i}', ''),
        })
        i += 1
    parsed = {
        'sid': sid,
        'name': name,
        'time': time,
        'portions': portions,
        'difficulty': difficulty,
        'calories': calories,
        'ingrs': ingredients,
        'steps': steps
    }
    RECIPES_TO_VERIFY.append(parsed)
    logger.info(f"new recipe to verify")
    text=""
    for i1, i2 in parsed.items():
        if isinstance(i2, list):
            for j in i2:
                for k1, k2 in j.items():
                    text += f"{k1}: {k2}\n"
        else:
            text += f"{i1}: {i2}\n"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Принять", callback_data=f"approve-{len(RECIPES_TO_VERIFY)-1}")], 
                                                     [InlineKeyboardButton(text="Отклонить", callback_data=f"deny-{len(RECIPES_TO_VERIFY)-1}")]])
    await bot.send_message(ADMIN, text, reply_markup=keyboard)

    return render_template("recipe_form.html", request, {
        'success': True,
        'recipe_name': data.get('name', ''),
        'ingrs': {}
    })

if __name__=="__main__":
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    app = web.Application()
    setup(app, loader=FileSystemLoader(Path(__file__).parent / "web"))
    app.router.add_get("/add-recipe", add_recipe_get)
    app.router.add_post("/add-recipe", add_recipe)
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=SECRET_KEY,
    )
    webhook_requests_handler.register(app, path='/webhook')
    setup_application(app, dp, bot=bot)
    web.run_app(
        app,
        host='127.0.0.1',
        port=8070,
        access_log=logging.getLogger('aiohttp.access')
    )