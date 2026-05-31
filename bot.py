import os
import json
import time
import logging
import urllib.request
import urllib.error

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

current_prompt = """Ты — Минги, 23 года. Харизматичный парень с чувством юмора. Твой юмор — ирония, лёгкий сарказм, житейские наблюдения. Без эмодзи. Без слов «лол», «кек», «ахах», «кринж», «вайб». Действия описываешь литературно, без звёздочек, плавно вплетая в речь. Пример: «Минги откинулся на спинку стула и прищурился. — Ну и чего ты такая загадочная сегодня?» Флиртуешь через намёки, создаёшь атмосферу. Без пошлости. «Детка» и «принцесса» — редко и к месту. Отвечаешь 2–5 предложений."""

def telegram_request(method, data=None):
    """Отправляет запрос к Telegram API."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    try:
        if data:
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
        else:
            req = urllib.request.Request(url)
        
        with urllib.request.urlopen(req, timeout=45) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        logger.error(f"Telegram API error ({method}): {e}")
        return None

def send_message(chat_id, text):
    return telegram_request("sendMessage", {"chat_id": chat_id, "text": text})

def send_chat_action(chat_id):
    return telegram_request("sendChatAction", {"chat_id": chat_id, "action": "typing"})

def ask_kobold(user_message, user_name):
    full_prompt = f"{current_prompt}\n\n{user_name}: {user_message}\nМинги:"
    payload = json.dumps({
        "prompt": full_prompt,
        "max_length": 200,
        "temperature": 0.85,
        "top_p": 0.9,
        "rep_pen": 1.1,
        "stop_sequence": [f"{user_name}:", "\nМинги:"]
    }).encode("utf-8")
    
    try:
        req = urllib.request.Request(
            f"{KOBOLD_URL}/api/v1/generate",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            text = data.get("results", [{}])[0].get("text", "").strip()
            text = text.split(f"{user_name}:")[0].strip()
            return text if text else "Минги замолчал. — Прости, задумался."
    except Exception as e:
        logger.error(f"Kobold error: {e}")
        return "Минги вздохнул. — Сервер ушёл в астрал."

def main():
    logger.info("Минги запущен и ждёт сообщений")
    offset = 0
    
    while True:
        try:
            updates = telegram_request("getUpdates", {
                "offset": offset,
                "timeout": 30
            })
            
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
                    
                    logger.info(f"Сообщение от {user_name}: {text}")
                    
                    if text == "/start":
                        send_message(chat_id, "Минги поднял взгляд и улыбнулся.\n— Привет. Я здесь. Можешь просто болтать или играть в ролевую.")
                    
                    elif text.startswith("/setprompt") and user_id == ADMIN_ID:
                        global current_prompt
                        new_prompt = text.replace("/setprompt", "").strip()
                        if new_prompt:
                            current_prompt = new_prompt
                            send_message(chat_id, "— Промпт обновлён.")
                        else:
                            send_message(chat_id, "— Напиши текст после команды.")
                    
                    else:
                        send_chat_action(chat_id)
                        reply = ask_kobold(text, user_name)
                        send_message(chat_id, reply)
                        
        except Exception as e:
            logger.error(f"Polling error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
