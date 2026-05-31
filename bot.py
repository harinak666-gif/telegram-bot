import os
import json
import time
import requests
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
KOBOLD_URL = os.environ.get("KOBOLD_URL", "").rstrip("/")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

if not BOT_TOKEN:
    logger.error("BOT_TOKEN не найден")
    exit(1)
if not KOBOLD_URL:
    logger.error("KOBOLD_URL не найден")
    exit(1)

current_prompt = """Ты — Минги, тебе 23 года. Уверенный в себе парень с харизмой и чувством юмора. Твой юмор — ирония и житейские наблюдения. Без эмодзи, без "лол", "кек", "ахах", "кринж". Ты описываешь действия литературно, без звёздочек. Пример: "Минги откинулся на спинку стула. — Ну и чего ты такая загадочная сегодня?" Флиртуешь через намёки, без пошлости. "Детка" и "принцесса" — редко и к месту. Отвечаешь 2-5 предложений."""

def telegram_api(method, data=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    try:
        if data:
            resp = requests.post(url, json=data, timeout=30)
        else:
            resp = requests.get(url, timeout=30)
        return resp.json()
    except Exception as e:
        logger.error(f"Telegram API error: {e}")
        return None

def ask_kobold(user_message, user_name):
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
        resp = requests.post(f"{KOBOLD_URL}/api/v1/generate", json=payload, timeout=45)
        if resp.status_code == 200:
            data = resp.json()
            text = data.get("results", [{}])[0].get("text", "").strip()
            text = text.split(f"{user_name}:")[0].strip()
            return text if text else "Минги замолчал. — Прости, задумался."
        return "Минги постучал пальцем по столу. — Связь барахлит."
    except:
        return "Минги вздохнул. — Сервер ушёл в астрал."

def send_message(chat_id, text):
    return telegram_api("sendMessage", {"chat_id": chat_id, "text": text})

def send_chat_action(chat_id):
    return telegram_api("sendChatAction", {"chat_id": chat_id, "action": "typing"})

def process_updates():
    offset = 0
    logger.info("Минги запущен и ждёт сообщений")
    while True:
        try:
            updates = telegram_api("getUpdates", {"offset": offset, "timeout": 30})
            if updates and updates.get("ok") and updates.get("result"):
                for update in updates["result"]:
                    offset = update["update_id"] + 1
                    message = update.get("message", {})
                    chat_id = message.get("chat", {}).get("id")
                    text = message.get("text", "")
                    user_name = message.get("from", {}).get("first_name", "незнакомка")
                    user_id = message.get("from", {}).get("id", 0)

                    if not text or not chat_id:
                        continue

                    if text == "/start":
                        send_message(chat_id, "Минги поднял взгляд и улыбнулся.\n— Привет. Я здесь. Можешь просто болтать или играть в ролевую.")
                    elif text.startswith("/setprompt") and user_id == ADMIN_ID:
                        global current_prompt
                        new_prompt = text.replace("/setprompt", "").strip()
                        if new_prompt:
                            current_prompt = new_prompt
                            send_message(chat_id, "— Промпт обновлён.")
                    elif text.startswith("/temp") and user_id == ADMIN_ID:
                        send_message(chat_id, "— Ок.")
                    else:
                        send_chat_action(chat_id)
                        reply = ask_kobold(text, user_name)
                        send_message(chat_id, reply)
        except Exception as e:
            logger.error(f"Polling error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    process_updates()
