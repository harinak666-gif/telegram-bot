import os
import telebot
import requests
from flask import Flask
import threading

# Токены из переменных окружения Render
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
CHARACTER_PROMPT = os.environ.get("CHARACTER_PROMPT", "Ты — дружелюбный ассистент.")  # описание персонажа

if not TELEGRAM_TOKEN or not GROQ_API_KEY:
    raise ValueError("Нужны TELEGRAM_TOKEN и GROQ_API_KEY в переменных окружения")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama3-8b-8192"  # бесплатная, быстрая, отлично держит роль

# Хранилище истории диалогов (сбрасывается при перезапуске, но для демо норм)
user_histories = {}

def get_response(chat_id, user_message):
    # Получаем историю или создаём новую
    if chat_id not in user_histories:
        user_histories[chat_id] = [{"role": "system", "content": CHARACTER_PROMPT}]
    
    # Добавляем сообщение пользователя
    user_histories[chat_id].append({"role": "user", "content": user_message})
    
    # Ограничиваем историю последними 20 сообщениями (чтобы не переполняться)
    if len(user_histories[chat_id]) > 21:  # system + 20 сообщений
        user_histories[chat_id] = user_histories[chat_id][:1] + user_histories[chat_id][-20:]
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": user_histories[chat_id],
        "temperature": 0.9,
        "max_tokens": 500
    }
    
    resp = requests.post(API_URL, headers=headers, json=payload, timeout=30)
    if resp.status_code == 200:
        answer = resp.json()["choices"][0]["message"]["content"]
        # Сохраняем ответ бота в историю
        user_histories[chat_id].append({"role": "assistant", "content": answer})
        return answer.strip()
    else:
        raise Exception(f"API error {resp.status_code}: {resp.text}")

@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.reply_to(message, "Привет! Я твой персонаж. Напиши мне что-нибудь.")

@bot.message_handler(commands=['reset'])
def reset_cmd(message):
    # Сброс истории – персонаж забывает контекст
    user_histories.pop(message.chat.id, None)
    bot.reply_to(message, "История сброшена. Давай начнём заново!")

@bot.message_handler(func=lambda m: True)
def chat(message):
    try:
        response = get_response(message.chat.id, message.text)
        bot.reply_to(message, response)
    except Exception as e:
        print(f"Ошибка: {e}")
        bot.reply_to(message, "Персонаж задумался... Повтори позже.")

# Обязательный веб-сервер для Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Бот-персонаж работает!"

threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000)).start()
bot.infinity_polling()
