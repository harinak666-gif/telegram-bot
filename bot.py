import os
import sys
import json
import time
import logging
import requests
from flask import Flask, request, jsonify

# ---------- Логи ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ---------- Конфиг из переменных окружения ----------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
KOBOLD_URL = os.environ.get("KOBOLD_URL", "").rstrip("/")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
PORT = int(os.environ.get("PORT", 10000))

# URL нашего сервиса на Render (нужно для установки вебхука)
# Либо берём из переменной, либо пытаемся угадать
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
if not WEBHOOK_URL:
    # На Render автоматически есть RENDER_EXTERNAL_URL
    WEBHOOK_URL = os.environ.get("RENDER_EXTERNAL_URL", "")
if not WEBHOOK_URL:
    logger.error("WEBHOOK_URL не задан! Укажи его в переменных окружения.")
    sys.exit(1)

WEBHOOK_URL = WEBHOOK_URL.rstrip("/")

# ---------- Системный промпт Минги ----------
SYSTEM_PROMPT = """Ты — Минги, 23 года. Харизматичный парень с чувством юмора. Твой юмор — ирония, лёгкий сарказм, житейские наблюдения. Без эмодзи. Без слов «лол», «кек», «ахах», «кринж», «вайб». Действия описываешь литературно, без звёздочек, плавно вплетая в речь. Пример: «Минги откинулся на спинку стула и прищурился. — Ну и чего ты такая загадочная сегодня?» Флиртуешь через намёки, создаёшь атмосферу. Без пошлости. «Детка» и «принцесса» — редко и к месту. Отвечаешь 2–5 предложений."""

# ---------- Вспомогательные функции ----------
def send_message(chat_id: int, text: str) -> bool:
    """Отправляет сообщение в Telegram с повторными попытками."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    for attempt in range(3):
        try:
            resp = requests.post(url, json=payload, timeout=30)
            if resp.status_code == 200:
                return True
            logger.error(f"sendMessage error {resp.status_code}: {resp.text}")
        except Exception as e:
            logger.error(f"sendMessage attempt {attempt+1}: {e}")
        time.sleep(2)
    return False

def send_chat_action(chat_id: int) -> None:
    """Отправляет 'typing...'"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendChatAction"
    payload = {"chat_id": chat_id, "action": "typing"}
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def ask_kobold(user_message: str, user_name: str) -> str:
    """Обращается к Kobold API и возвращает ответ."""
    full_prompt = f"{SYSTEM_PROMPT}\n\n{user_name}: {user_message}\nМинги:"
    payload = {
        "prompt": full_prompt,
        "max_length": 200,
        "temperature": 0.85,
        "top_p": 0.9,
        "rep_pen": 1.1,
        "stop_sequence": [f"{user_name}:", "\nМинги:"]
    }
    try:
        resp = requests.post(f"{KOBOLD_URL}/api/v1/generate", json=payload, timeout=45)
        if resp.status_code == 200:
            data = resp.json()
            text = data.get("results", [{}])[0].get("text", "").strip()
            text = text.split(f"{user_name}:")[0].strip()
            return text if text else "Минги замолчал. — Прости, задумался."
        else:
            logger.error(f"Kobold status {resp.status_code}")
            return "Минги постучал пальцем по столу. — Связь барахлит."
    except Exception as e:
        logger.error(f"Kobold error: {e}")
        return "Минги вздохнул. — Сервер ушёл в астрал."

# ---------- Flask приложение ----------
app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    """Обрабатывает входящие обновления от Telegram."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "no data"}), 200

        message = data.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")
        user_name = message.get("from", {}).get("first_name", "незнакомка")
        user_id = message.get("from", {}).get("id", 0)

        if not chat_id or not text:
            return jsonify({"status": "ignored"}), 200

        logger.info(f"Сообщение от {user_name} ({user_id}): {text}")

        if text == "/start":
            send_message(chat_id,
                "Минги поднял взгляд и улыбнулся.\n— Привет. Я здесь. Можешь просто болтать или играть в ролевую.")
        elif text.startswith("/setprompt") and user_id == ADMIN_ID:
            global SYSTEM_PROMPT
            new_prompt = text.replace("/setprompt", "").strip()
            if new_prompt:
                SYSTEM_PROMPT = new_prompt
                send_message(chat_id, "— Промпт обновлён.")
            else:
                send_message(chat_id, "— Напиши текст после команды.")
        else:
            send_chat_action(chat_id)
            reply = ask_kobold(text, user_name)
            send_message(chat_id, reply)

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({"status": "error"}), 500

@app.route("/", methods=["GET"])
def index():
    return "Минги работает!", 200

# ---------- Установка вебхука при старте ----------
def set_webhook():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    webhook_endpoint = f"{WEBHOOK_URL}/webhook"
    payload = {"url": webhook_endpoint}
    for attempt in range(5):
        try:
            resp = requests.post(url, json=payload, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok"):
                    logger.info(f"Вебхук установлен: {webhook_endpoint}")
                    return True
            logger.error(f"Ошибка установки вебхука: {resp.text}")
        except Exception as e:
            logger.error(f"Attempt {attempt+1}: {e}")
        time.sleep(3)
    return False

def delete_webhook():
    """Удаляет вебхук (чтобы не висел старый)."""
    requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook")

if __name__ == "__main__":
    logger.info("Запуск Минги...")

    # Сначала удаляем старый вебхук, чтобы не было конфликтов
    delete_webhook()
    time.sleep(1)

    if not set_webhook():
        logger.error("Не удалось установить вебхук. Проверь WEBHOOK_URL и доступность Telegram.")
        sys.exit(1)

    logger.info(f"Минги слушает порт {PORT}...")
    app.run(host="0.0.0.0", port=PORT)
