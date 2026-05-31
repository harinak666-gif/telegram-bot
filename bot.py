import os
import time
import logging
import requests
import telebot
from telebot import types

# ---------- Настройка логирования ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ---------- Конфигурация ----------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
KOBOLD_URL = os.environ.get("KOBOLD_URL", "").rstrip("/")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

if not BOT_TOKEN:
    logger.error("BOT_TOKEN не найден")
    exit(1)
if not KOBOLD_URL:
    logger.error("KOBOLD_URL не найден")
    exit(1)

# ---------- Инициализация бота ----------
bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

# ---------- Системный промпт ----------
current_prompt = (
    "Ты — Минги, 23 года. Харизматичный парень с чувством юмора. "
    "Твой юмор — ирония, лёгкий сарказм, житейские наблюдения. "
    "Без эмодзи. Без слов «лол», «кек», «ахах», «кринж», «вайб». "
    "Действия описываешь литературно, без звёздочек, плавно вплетая в речь. "
    "Пример: «Минги откинулся на спинку стула и прищурился. — Ну и чего ты такая загадочная сегодня?» "
    "Флиртуешь через намёки, создаёшь атмосферу. Без пошлости. "
    "«Детка» и «принцесса» — редко и к месту. Отвечаешь 2–5 предложений."
)

# ---------- Вспомогательные функции ----------
def ask_kobold(user_message, user_name):
    """Отправляет запрос в Kobold и возвращает ответ."""
    full_prompt = f"{current_prompt}\n\n{user_name}: {user_message}\nМинги:"
    payload = {
        "prompt": full_prompt,
        "max_length": 200,
        "temperature": 0.85,
        "top_p": 0.9,
        "rep_pen": 1.1,
        "stop_sequence": [f"{user_name}:", "\nМинги:"]
    }
    try:
        resp = requests.post(
            f"{KOBOLD_URL}/api/v1/generate",
            json=payload,
            timeout=45
        )
        if resp.status_code == 200:
            data = resp.json()
            text = data.get("results", [{}])[0].get("text", "").strip()
            text = text.split(f"{user_name}:")[0].strip()
            return text if text else "Минги замолчал. — Прости, задумался."
        else:
            logger.error(f"Kobold status {resp.status_code}: {resp.text}")
            return "Минги постучал пальцем по столу. — Связь барахлит."
    except Exception as e:
        logger.error(f"Kobold error: {e}")
        return "Минги вздохнул. — Сервер ушёл в астрал."

# ---------- Обработчики команд ----------
@bot.message_handler(commands=["start"])
def handle_start(message):
    bot.send_message(
        message.chat.id,
        "Минги поднял взгляд и улыбнулся.\n"
        "— Привет. Я здесь. Можешь просто болтать или играть в ролевую."
    )

@bot.message_handler(commands=["setprompt"])
def handle_setprompt(message):
    global current_prompt
    if message.from_user.id != ADMIN_ID:
        return
    new_prompt = message.text.replace("/setprompt", "").strip()
    if new_prompt:
        current_prompt = new_prompt
        bot.reply_to(message, "— Промпт обновлён.")
    else:
        bot.reply_to(message, "— Напиши текст после команды.")

@bot.message_handler(commands=["temp"])
def handle_temp(message):
    if message.from_user.id != ADMIN_ID:
        return
    bot.reply_to(message, "— Температура фиксирована на 0.85. Пока так.")

# ---------- Обработчик текстовых сообщений ----------
@bot.message_handler(content_types=["text"])
def handle_text(message):
    user_msg = message.text
    user_name = message.from_user.first_name or "незнакомка"

    # Имитируем "печатает..."
    bot.send_chat_action(message.chat.id, "typing")

    reply = ask_kobold(user_msg, user_name)
    bot.send_message(message.chat.id, reply)

# ---------- Запуск ----------
if __name__ == "__main__":
    logger.info("Запуск Минги...")

    # Удаляем вебхук на всякий случай и запускаем поллинг
    bot.remove_webhook()
    time.sleep(1)

    logger.info("Минги запущен и слушает через long polling")
    while True:
        try:
            bot.infinity_polling(timeout=30, long_polling_timeout=30)
        except Exception as e:
            logger.error(f"Поллинг упал: {e}")
            time.sleep(5)
            # Перезапустим поллинг
            continue
