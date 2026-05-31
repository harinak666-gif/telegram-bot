import os
import telebot
import requests
import random
from flask import Flask
import threading

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Gemini бесплатная модель
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

RANDOM_STYLES = [
    "Придумай короткий смешной факт.",
    "Расскажи анекдот в одном предложении.",
    "Напиши философскую мысль дня.",
    "Скажи что-то мотивирующее.",
    "Придумай странный вопрос для размышления.",
    "Опиши погоду на вымышленной планете.",
]

# Запасные фразы
FALLBACK = [
    "Слоны не умеют прыгать, но отлично плавают! 🐘",
    "Бананы радиоактивны, но нужно съесть 10 миллионов за раз. 🍌",
    "Кенгуру не умеют ходить назад. 🦘",
    "Лучшее время посадить дерево — сейчас! 🌳",
]

def generate(prompt):
    if not GEMINI_API_KEY:
        return None
    try:
        url = f"{GEMINI_URL}?key={GEMINI_API_KEY}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 100, "temperature": 0.9}
        }
        resp = requests.post(url, json=payload, timeout=20)
        if resp.status_code == 200:
            return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        else:
            print(f"Gemini error: {resp.status_code} {resp.text}")
            return None
    except Exception as e:
        print(f"Exception: {e}")
        return None

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Привет! Я ИИ-бот. Напиши мне что-нибудь!")

@bot.message_handler(func=lambda m: True)
def reply(message):
    prompt = random.choice(RANDOM_STYLES)
    text = generate(prompt)
    if text:
        bot.reply_to(message, text)
    else:
        bot.reply_to(message, random.choice(FALLBACK))

app = Flask(__name__)

@app.route('/')
def home():
    return "OK"

threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000)).start()
bot.infinity_polling()
