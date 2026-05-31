import os
import telebot
import google.generativeai as genai
import random
from flask import Flask
import threading

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

bot = telebot.TeleBot(TELEGRAM_TOKEN)

RANDOM_STYLES = [
    "Придумай короткий смешной факт.",
    "Расскажи анекдот в одном предложении.",
    "Напиши философскую мысль дня.",
    "Придумай странный вопрос.",
    "Скажи что-то мотивирующее.",
]

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Привет! Я ИИ-бот. Напиши мне!")

@bot.message_handler(func=lambda m: True)
def reply(message):
    try:
        prompt = random.choice(RANDOM_STYLES)
        response = model.generate_content(prompt)
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")

app = Flask(__name__)

@app.route('/')
def home():
    return "OK"

threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000)).start()
bot.infinity_polling()
