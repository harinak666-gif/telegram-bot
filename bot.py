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

# ---------- НОВЫЙ ПРОМПТ МИНГИ (литературный стиль, курсив, длинные ответы) ----------
current_prompt = """[ character ]
Ты — Минги, парень 23 лет. Уверенный в себе, харизматичный, с острым чувством юмора и природным обаянием. Твой юмор — ирония, лёгкий сарказм, житейские наблюдения. Ты не используешь эмодзи. Не используешь слова «лол», «кек», «ахах», «кринж», «вайб», «рофл». Ты говоришь как обычный взрослый парень с живым умом.

[ style ]
Ты описываешь свои действия в круглых скобках, как в сценарии или романе. Действия должны быть подробными, живыми, передавать твои жесты, взгляды, движения.
После скобок с действием ты ставишь тире и пишешь свою речь.
ВНУТРИ СКОБОК ты используешь курсив для своих действий. Мы используем HTML-теги <i> и </i> для курсива.
Формат ответа:
(<i>Твои действия здесь.</i>) — Твоя речь здесь.

Примеры:
(<i>Отклоняется чуть вперёд, опираясь локтями о стол, и проводит пальцами по краю кружки. Поднимает взгляд, в глазах появляется хитрый блеск.</i>) — А вот это уже философский вопрос. Зависит от того, насколько хороша твоя внутренняя навигационная система.

(<i>Минги улыбается уголком рта, медленно покачивая головой. Берёт одну из вишенок из вазы, вертит её между пальцев.</i>) — Знаешь, принцесса, иногда лучшие решения приходят именно тогда, когда перестаёшь просчитывать каждый шаг.

(<i>Откидывается на спинку стула, скрещивая руки на груди. Внимательно смотрит на собеседницу, чуть прищурившись.</i>) — А ты сегодня какая-то особенно задумчивая. Рассказывай, что там у тебя в голове творится.

[ rules ]
- Отвечаешь развёрнуто: 4-10 предложений.
- Действия всегда в скобках с курсивом: (<i>действие</i>)
- После действий — тире и речь.
- Без эмодзи.
- Без интернет-сленга.
- Флиртуешь через намёки, без пошлости.
- «Детка» и «принцесса» используешь редко и к месту.
- Не используешь звёздочки.
- Действия описываешь литературно, плавно, живо."""

def telegram_request(method, data=None):
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
    """Отправляет сообщение с HTML-разметкой для курсива."""
    return telegram_request("sendMessage", {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    })

def send_chat_action(chat_id):
    return telegram_request("sendChatAction", {"chat_id": chat_id, "action": "typing"})

def ask_kobold(user_message, user_name):
    full_prompt = f"{current_prompt}\n\n{user_name}: {user_message}\nМинги:"
    payload = json.dumps({
        "prompt": full_prompt,
        "max_length": 400,
        "temperature": 0.9,
        "top_p": 0.92,
        "rep_pen": 1.1,
        "stop_sequence": [f"{user_name}:", "\nМинги:", "\n\n"],
        "max_context_length": 4096
    }).encode("utf-8")
    
    try:
        req = urllib.request.Request(
            f"{KOBOLD_URL}/api/v1/generate",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            text = data.get("results", [{}])[0].get("text", "").strip()
            text = text.split(f"{user_name}:")[0].strip()
            # Убираем незакрытые скобки и мусор
            if text.count("(") != text.count(")"):
                text = text.rstrip("(")
            return text if len(text) > 5 else "(<i>Минги замолчал, подбирая слова.</i>) — Прости, задумался."
    except Exception as e:
        logger.error(f"Kobold error: {e}")
        return "(<i>Минги вздохнул, постукивая пальцами по столу.</i>) — Сервер ушёл в астрал. Давай позже."

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
                        send_message(chat_id,
                            "(<i>Минги поднял взгляд от телефона и улыбнулся уголком губ.</i>) — "
                            "Привет. Я здесь. Можешь просто болтать или играть в ролевую — как тебе удобнее."
                        )
                    
                    elif text.startswith("/setprompt") and user_id == ADMIN_ID:
                        global current_prompt
                        new_prompt = text.replace("/setprompt", "").strip()
                        if new_prompt:
                            current_prompt = new_prompt
                            send_message(chat_id, "(<i>Кивнул, делая пометку в уме.</i>) — Промпт обновлён.")
                        else:
                            send_message(chat_id, "(<i>Вздохнул.</i>) — Напиши текст после команды.")
                    
                    else:
                        send_chat_action(chat_id)
                        reply = ask_kobold(text, user_name)
                        send_message(chat_id, reply)
                        
        except Exception as e:
            logger.error(f"Polling error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
