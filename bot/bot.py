import telebot
from telebot import types
from config import TOKEN
from kb_operations import Operator, Connector

bot = telebot.TeleBot(TOKEN)
op = Operator()
conn = Connector()

@bot.message_handler(commands=['start'])
def start(message: types.Message):
    op.add_user(message.from_user.id, message.from_user.full_name)
    bot.send_message(message.from_user.id, "1234")

@bot.message_handler()
def handle(message: types.Message):
    op.add_message(message.from_user.id, message.text)

def test(text):
    bot.send_message(1862958404, text)

if __name__=="__main__":
    conn.safe_connect('ws://localhost:8090')
    conn.subscribe_to_message(bot.send_message)
    bot.polling(none_stop=True)