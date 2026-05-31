import os
import telebot
import random
from flask import Flask
import threading

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

if not TELEGRAM_TOKEN:
    raise ValueError("Токен не найден! Добавьте TELEGRAM_TOKEN в переменные окружения Render")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

phrases = [
    "Привет! Я работаю на Render! 🌟",
    "Ура! Всё получилось! 🎉",
    "Случайная мысль от бота!",
    "Какой чудесный день! ☀️",
    "Бот активен 24/7!",
    "Знаете ли вы, что слоны не умеют прыгать?",
    "Лучшая мотивация — начать с малого!",
]

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Привет! Я бот на Render! Напиши мне 😊")

@bot.message_handler(func=lambda m: True)
def reply(message):
    bot.reply_to(message, random.choice(phrases))

app = Flask(__name__)

@app.route('/')
def home():
    return "Бот работает!"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

threading.Thread(target=run_flask).start()

print("Бот запущен!")
bot.infinity_polling()
