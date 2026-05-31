import os
import telebot
import requests
import random
from flask import Flask
import threading

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
DEEPINFRA_API_KEY = os.environ.get("DEEPINFRA_API_KEY")  # можно оставить пустым для публичных моделей

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Бесплатная модель (можно сменить на другую)
MODEL = "mistralai/Mixtral-8x7B-Instruct-v0.1"  # или "meta-llama/Llama-3-8b-chat-hf"
API_URL = f"https://api.deepinfra.com/v1/openai/chat/completions"

RANDOM_STYLES = [
    "Придумай короткий смешной факт.",
    "Расскажи анекдот в одном предложении.",
    "Напиши философскую мысль дня.",
    "Скажи что-то мотивирующее.",
]

def generate(prompt):
    headers = {"Content-Type": "application/json"}
    if DEEPINFRA_API_KEY:
        headers["Authorization"] = f"Bearer {DEEPINFRA_API_KEY}"
    data = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 150,
        "temperature": 0.9
    }
    resp = requests.post(API_URL, headers=headers, json=data, timeout=30)
    if resp.status_code == 200:
        return resp.json()["choices"][0]["message"]["content"].strip()
    else:
        raise Exception(f"API error {resp.status_code}: {resp.text}")

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Привет! Я ИИ-бот на бесплатной модели. Напиши мне!")

@bot.message_handler(func=lambda m: True)
def reply(message):
    prompt = random.choice(RANDOM_STYLES)
    try:
        text = generate(prompt)
        bot.reply_to(message, text)
    except Exception as e:
        bot.reply_to(message, "ИИ временно задумался... Попробуй позже.")
        print(e)

app = Flask(__name__)
@app.route('/')
def home(): return "OK"
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000)).start()
bot.infinity_polling()
