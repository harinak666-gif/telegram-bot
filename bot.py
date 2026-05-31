import os
import telebot
from openai import OpenAI
import random
from flask import Flask
import threading

# Токены из переменных окружения Render
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")

if not TELEGRAM_TOKEN or not DEEPSEEK_API_KEY:
    raise ValueError("Добавьте TELEGRAM_TOKEN и DEEPSEEK_API_KEY в Environment Variables")

# Подключаем DeepSeek
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Стили для случайных мыслей
RANDOM_STYLES = [
    "Придумай короткий смешной факт (1-2 предложения).",
    "Расскажи анекдот (коротко).",
    "Напиши философскую мысль дня.",
    "Придумай странный вопрос для размышления.",
    "Скажи что-то мотивирующее и необычное.",
    "Опиши погоду на вымышленной планете.",
    "Дай безумный кулинарный совет.",
]

def get_ai_text(prompt):
    """Запрос к DeepSeek"""
    response = client.chat.completions.create(
        model="deepseek-chat",  # Основная модель DeepSeek
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.8,  # Случайность
        max_tokens=150
    )
    return response.choices[0].message.content.strip()

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Привет! Я ИИ-бот на DeepSeek. Напиши мне, и я отвечу случайной мыслью. Или команда /random")

@bot.message_handler(commands=['random'])
def random_cmd(message):
    prompt = random.choice(RANDOM_STYLES)
    try:
        answer = get_ai_text(prompt)
        bot.reply_to(message, answer)
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")

@bot.message_handler(func=lambda m: True)
def reply(message):
    prompt = random.choice(RANDOM_STYLES)
    try:
        answer = get_ai_text(prompt)
        bot.reply_to(message, answer)
    except:
        bot.reply_to(message, "ИИ задумался... Попробуй ещё!")

# Flask для Render
app = Flask(__name__)

@app.route('/')
def home():
    return "ИИ-бот на DeepSeek работает!"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

threading.Thread(target=run_flask).start()
print("Бот на DeepSeek запущен!")
bot.infinity_polling()
