import os
import telebot
import openai
import random
import time
from flask import Flask
import threading

# Токены из переменных окружения
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if not TELEGRAM_TOKEN or not OPENAI_API_KEY:
    raise ValueError("Добавьте TELEGRAM_TOKEN и OPENAI_API_KEY в Environment Variables")

openai.api_key = OPENAI_API_KEY
bot = telebot.TeleBot(TELEGRAM_TOKEN)

RANDOM_STYLES = [
    "Придумай короткий смешной факт.",
    "Расскажи анекдот в одном предложении.",
    "Напиши философскую мысль дня.",
    "Придумай странный вопрос для размышления.",
    "Скажи что-то мотивирующее и необычное.",
    "Опиши погоду на вымышленной планете.",
    "Дай безумный кулинарный совет.",
]

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Привет! Я ИИ-бот. Напиши мне что угодно, и я отвечу случайной мыслью.")

@bot.message_handler(commands=['random'])
def random_cmd(message):
    prompt = random.choice(RANDOM_STYLES)
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.9
        )
        bot.reply_to(message, response.choices[0].message.content.strip())
    except Exception as e:
        bot.reply_to(message, "ИИ задумался, попробуй позже...")

@bot.message_handler(func=lambda m: True)
def reply(message):
    prompt = random.choice(RANDOM_STYLES)
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.9
        )
        bot.reply_to(message, response.choices[0].message.content.strip())
    except Exception as e:
        bot.reply_to(message, "ИИ временно задумался... Попробуй ещё раз!")

# Flask для Render
app = Flask(__name__)

@app.route('/')
def home():
    return "ИИ-бот работает!"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

threading.Thread(target=run_flask).start()
print("ИИ-бот запущен на Render!")
bot.infinity_polling()
