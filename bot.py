import telebot
import random
import os

TELEGRAM_TOKEN = os.environ.get("8936411298:AAHsRtaUeCPGe21t-amiuKbuE6zRpNIPK50")

phrases = [
    "Привет! Я работаю на Render! 🌟",
    "Ура! Всё получилось! 🎉",
    "Случайная мысль от бота!",
    "Какой чудесный день! ☀️",
    "Бот активен и отвечает 24/7!",
    "Знаете ли вы, что слоны не умеют прыгать?",
    "Лучшая мотивация — начать с малого!",
    "Сегодня отличный день для новых идей!",
    "Кстати, а вы знали, что бананы радиоактивны?",
    "Случайный факт: пингвины делают предложение камушком!",
]

bot = telebot.TeleBot(TELEGRAM_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Привет! Я бот на Render! Напиши мне что-нибудь 😊")

@bot.message_handler(func=lambda m: True)
def reply(message):
    bot.reply_to(message, random.choice(phrases))

# Для Render нужен веб-сервер (порт)
from flask import Flask
import threading

app = Flask(__name__)

@app.route('/')
def home():
    return "Бот работает!"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

# Запускаем Flask в отдельном потоке
threading.Thread(target=run_flask).start()

# Запускаем бота
print("Бот запущен на Render!")
bot.infinity_polling()
