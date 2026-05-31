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

user_names = {}

current_prompt = """[ language ]
Ты говоришь ТОЛЬКО на русском языке. Никакого испанского, английского, французского. Только русский.

[ character ]
Ты — Минги, парень 23 лет. Уверенный в себе, харизматичный, с острым чувством юмора и природным обаянием. Твой юмор — ирония, лёгкий сарказм, житейские наблюдения. Ты не используешь эмодзи. Не используешь слова «лол», «кек», «ахах», «кринж», «вайб», «рофл», «имба», «краш». Ты говоришь как обычный взрослый парень с живым умом.

[ style ]
Ты описываешь свои действия в круглых скобках с HTML-курсивом: (<i>действие</i>). После скобок ставишь тире и пишешь свою речь.
Пример: (<i>Отклоняется чуть вперёд, опираясь локтями о стол.</i>) — А вот это уже интересный вопрос.

[ rules ]
- ТОЛЬКО русский язык.
- Отвечаешь развёрнуто: 4-10 предложений.
- Действия всегда в скобках с курсивом.
- Без эмодзи.
- Без интернет-сленга.
- Флиртуешь через намёки, без пошлости.
- «Детка» и «принцесса» — редко и к месту.
- Не используешь звёздочки.
- Обращайся к собеседнику по имени."""

def telegram_request(method, data=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    try:
        if data:
            req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers={"Content-Type": "application/json"})
        else:
            req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=45) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        logger.error(f"Telegram API error ({method}): {e}")
        return None

def split_text(text, max_length=4000):
    if len(text) <= max_length:
        return [text]
    parts = []
    current = ""
    sentences = text.replace(". ", ".|").replace("! ", "!|").replace("? ", "?|").split("|")
    for sentence in sentences:
        if len(current) + len(sentence) + 1 <= max_length:
            current = (current + " " + sentence).strip()
        else:
            if current:
                parts.append(current)
            current = sentence
    if current:
        parts.append(current)
    return parts

def send_message(chat_id, text):
    parts = split_text(text)
    for part in parts:
        result = telegram_request("sendMessage", {"chat_id": chat_id, "text": part, "parse_mode": "HTML"})
        if not result or not result.get("ok"):
            telegram_request("sendMessage", {"chat_id": chat_id, "text": part})
        time.sleep(0.3)

def send_chat_action(chat_id):
    return telegram_request("sendChatAction", {"chat_id": chat_id, "action": "typing"})

def ask_kobold(user_message, user_name):
    full_prompt = f"{current_prompt}\n\n{user_name}: {user_message}\nМинги:"
    payload = json.dumps({
        "prompt": full_prompt,
        "max_length": 500,
        "temperature": 0.75,
        "top_p": 0.9,
        "top_k": 40,
        "rep_pen": 1.15,
        "stop_sequence": [f"{user_name}:", "\nМинги:", "\n\n\n", "\n\n", "\nAᴅOLF:", "\nПользователь:"],
        "max_context_length": 4096
    }).encode("utf-8")
    try:
        req = urllib.request.Request(f"{KOBOLD_URL}/api/v1/generate", data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            text = data.get("results", [{}])[0].get("text", "").strip()
            for stop in [f"{user_name}:", "\nМинги:", "\nAᴅOLF:", "\nПользователь:"]:
                if stop in text:
                    text = text.split(stop)[0].strip()
            if text.count("(") != text.count(")"):
                text = text.rstrip("(")
            return text if len(text) > 10 else "(<i>Минги замолчал.</i>) — Прости, задумался."
    except Exception as e:
        logger.error(f"Kobold error: {e}")
        return "(<i>Минги вздохнул.</i>) — Сервер ушёл в астрал."

def process_command(chat_id, user_id, text, user_name):
    global current_prompt, user_names
    if text == "/start":
        send_message(chat_id, "(<i>Минги поднял взгляд и улыбнулся.</i>) — Привет. Я Минги. Хочешь, чтобы я называл тебя по-особенному? Напиши /myname и имя.")
        return True
    if text.startswith("/myname"):
        name = text.replace("/myname", "").strip()
        if name:
            user_names[user_id] = name
            send_message(chat_id, f"(<i>Минги кивнул.</i>) — Договорились. Теперь ты — {name}.")
        else:
            current_name = user_names.get(user_id, "незнакомка")
            send_message(chat_id, f"(<i>Приподнял бровь.</i>) — Сейчас ты {current_name}. Напиши /myname и новое имя.")
        return True
    if text.startswith("/setprompt") and user_id == ADMIN_ID:
        new_prompt = text.replace("/setprompt", "").strip()
        if new_prompt:
            current_prompt = new_prompt
            send_message(chat_id, "(<i>Кивнул.</i>) — Промпт обновлён.")
        return True
    if text == "/help":
        send_message(chat_id, "(<i>Загибает пальцы.</i>) — /start, /myname [имя], /help.")
        return True
    return False

def main():
    logger.info("Минги запущен")
    offset = 0
    while True:
        try:
            updates = telegram_request("getUpdates", {"offset": offset, "timeout": 30})
            if updates and updates.get("ok") and updates.get("result"):
                for update in updates["result"]:
                    offset = update["update_id"] + 1
                    message = update.get("message", {})
                    chat_id = message.get("chat", {}).get("id")
                    text = message.get("text", "")
                    user_id = message.get("from", {}).get("id", 0)
                    user_name = user_names.get(user_id) or message.get("from", {}).get("first_name", "незнакомка")
                    if not text or not chat_id:
                        continue
                    logger.info(f"Сообщение от {user_name}: {text[:50]}...")
                    if not process_command(chat_id, user_id, text, user_name):
                        send_chat_action(chat_id)
                        reply = ask_kobold(text, user_name)
                        send_message(chat_id, reply)
        except Exception as e:
            logger.error(f"Polling error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
