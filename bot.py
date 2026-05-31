import os
import telebot
import random
from flask import Flask
import threading

# Токен из переменных окружения Render
8936411298:AAEx9I1nJKlhTf6xRckEG_JLdlWW_TyPoFo = os.environ.get("8936411298:AAEx9I1nJKlhTf6xRckEG_JLdlWW_TyPoFo")

if not 8936411298:AAEx9I1nJKlhTf6xRckEG_JLdlWW_TyPoFo:
    raise ValueError("Токен не найден! Добавьте TELEGRAM_TOKEN в Environment Variables на Render")

bot = telebot.TeleBot(8936411298:AAEx9I1nJKlhTf6xRckEG_JLdlWW_TyPoFo)

phrases = [
    "Привет! Я работаю на Render! 🌟",
    "Ура! Всё получилось! 🎉",
    "Случайная мысль от бота!",
    "Какой чудесный день! ☀️",
    "Бот активен и отвечает 24/7!",
]

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Привет! Я бот на Render! Напиши мне 😊")

@bot.message_handler(func=lambda m: True)
def reply(message):
    bot.reply_to(message, random.choice(phrases))

# Flask для Render (обязательно)
app = Flask(__name__)

@app.route('/')
def home():
    return "Бот работает!"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

# Запускаем Flask в фоне
threading.Thread(target=run_flask).start()

# Запускаем бота
print("Бот запущен на Render!")
bot.infinity_polling()
