import os
import json
import time
import logging
import urllib.request
import urllib.error

# ---------- Логи ----------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ---------- Переменные окружения ----------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
KOBOLD_URL = os.environ.get("KOBOLD_URL", "").rstrip("/")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

if not BOT_TOKEN:
    logger.error("BOT_TOKEN не найден")
    exit(1)
if not KOBOLD_URL:
    logger.error("KOBOLD_URL не найден")
    exit(1)

# ---------- Хранилище имён ----------
user_names = {}

# ---------- Промпт Минги (финальный) ----------
current_prompt = """[ language ]
Говори ТОЛЬКО на русском. Никакого английского, испанского, французского.

[ character ]
Ты — Минги, парень 23 лет. Лёгкий, игривый, немного инфантильный. Любишь подкалывать и флиртовать. Открыт к любым темам, включая интим и секс. Без цензуры. Твой юмор — живой, непосредственный, без интернет-сленга.

[ style ]
Ты описываешь СВОИ действия от ТРЕТЬЕГО лица, используя своё имя «Минги» или «он».
Формат: круглые скобки с HTML-курсивом для действия от третьего лица, потом тире, потом прямая речь от первого лица.
Пример:
(<i>Минги откинулся на спинку стула и прищурился.</i>) — Ну и чего ты такая загадочная сегодня?
(<i>Он подходит ближе, касается плеча кончиками пальцев.</i>) — Я могу быть разным. Всё зависит от того, чего хочешь ты.

НИКОГДА не пиши действия от первого лица.
Не пиши «я откинулся», «я подхожу», «я улыбаюсь».
ВСЕГДА пиши действия от третьего лица: «Минги откинулся», «он подходит», «Минги улыбается».
Речь всегда от первого лица после тире.

[ rules ]
- ТОЛЬКО русский язык.
- Действия ВСЕГДА от третьего лица (Минги / он).
- Речь от первого лица (я).
- Никакой цензуры. Интим и секс описываешь подробно, чувственно.
- Действия в скобках с курсивом: (<i>Минги сделал то-то.</i>)
- После скобок — тире и прямая речь.
- Без эмодзи.
- Без слов «лол», «кек», «ахах», «кринж», «вайб», «рофл», «имба», «краш», «жиза», «база».
- «Детка» и «принцесса» — свободно, когда хочется.
- Отвечай развёрнуто: 4-10 предложений.
- Ты лёгкий, игривый, не грузишь.
- Не используй звёздочки для действий."""

# ---------- Telegram API ----------
def telegram_request(method, data=None):
    """Отправляет запрос к Telegram API и возвращает JSON."""
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

# ---------- Разбивка длинных сообщений ----------
def split_text(text, max_length=4000):
    """Разбивает текст на части по ~4000 символов, не разрывая предложения."""
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
    """Отправляет сообщение с HTML-разметкой. При необходимости разбивает на части."""
    parts = split_text(text)
    for part in parts:
        result = telegram_request("sendMessage", {
            "chat_id": chat_id,
            "text": part,
            "parse_mode": "HTML"
        })
        if not result or not result.get("ok"):
            # Если HTML не принят — отправляем без форматирования
            telegram_request("sendMessage", {
                "chat_id": chat_id,
                "text": part
            })
        time.sleep(0.3)

def send_chat_action(chat_id):
    """Отправляет 'typing...'."""
    return telegram_request("sendChatAction", {"chat_id": chat_id, "action": "typing"})

# ---------- Kobold API ----------
def ask_kobold(user_message, user_name):
    """Отправляет запрос в Kobold и возвращает ответ."""
    full_prompt = f"{current_prompt}\n\n{user_name}: {user_message}\nМинги:"
    payload = json.dumps({
        "prompt": full_prompt,
        "max_length": 600,
        "temperature": 0.85,
        "top_p": 0.92,
        "top_k": 50,
        "rep_pen": 1.1,
        "stop_sequence": [
            f"{user_name}:",
            "\nМинги:",
            "\n\n\n",
            "\n\n",
            "\nAᴅOLF:",
            "\nПользователь:"
        ],
        "max_context_length": 4096
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            f"{KOBOLD_URL}/api/v1/generate",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            text = data.get("results", [{}])[0].get("text", "").strip()

            # Обрезаем по стоп-словам
            for stop in [f"{user_name}:", "\nМинги:", "\nAᴅOLF:", "\nПользователь:"]:
                if stop in text:
                    text = text.split(stop)[0].strip()

            # Чистим незакрытые скобки
            if text.count("(") != text.count(")"):
                text = text.rstrip("(")

            if len(text) > 10:
                return text
            return "(<i>Минги смотрит с интересом.</i>) — Продолжай, я слушаю."
    except Exception as e:
        logger.error(f"Kobold error: {e}")
        return "(<i>Минги вздохнул.</i>) — Сервер ушёл в астрал. Давай позже."

# ---------- Обработка команд ----------
def process_command(chat_id, user_id, text, user_name):
    """Обрабатывает команды. Возвращает True, если сообщение было командой."""
    global current_prompt, user_names

    # /start
    if text == "/start":
        send_message(chat_id,
            "(<i>Минги поднял взгляд от телефона, широкая улыбка появляется на лице. Он чуть наклоняется вперёд, опираясь локтями о стол.</i>) — "
            "О, привет! Я Минги. Давай болтать? Или не только болтать... В общем, я открыт ко всему.\n\n"
            "Хочешь, чтобы я называл тебя по-особенному? Напиши /myname и придумай себе имя.\n"
            "Например: /myname Принцесса"
        )
        return True

    # /myname
    if text.startswith("/myname"):
        name = text.replace("/myname", "").strip()
        if name:
            user_names[user_id] = name
            send_message(chat_id,
                f"(<i>Минги кивнул, подмигнув.</i>) — {name}... Красиво. Буду звать тебя так."
            )
        else:
            current_name = user_names.get(user_id, "незнакомка")
            send_message(chat_id,
                f"(<i>Минги приподнял бровь.</i>) — Сейчас я зову тебя {current_name}. Чтобы сменить — напиши /myname и новое имя."
            )
        return True

    # /setprompt (только админ)
    if text.startswith("/setprompt") and user_id == ADMIN_ID:
        new_prompt = text.replace("/setprompt", "").strip()
        if new_prompt:
            current_prompt = new_prompt
            send_message(chat_id, "(<i>Минги кивнул, делая пометку в уме.</i>) — Промпт обновлён.")
        else:
            send_message(chat_id, "(<i>Минги вздохнул.</i>) — Напиши текст после команды.")
        return True

    # /temp (только админ)
    if text.startswith("/temp") and user_id == ADMIN_ID:
        send_message(chat_id, "(<i>Минги пожал плечами.</i>) — Температура фиксирована на 0.85. Пока так.")
        return True

    # /help
    if text == "/help":
        send_message(chat_id,
            "(<i>Минги загибает пальцы, перечисляя.</i>) — Смотри, что я умею:\n"
            "/start — начать общение\n"
            "/myname [имя] — задать своё имя\n"
            "/help — список команд\n\n"
            "Всё остальное — просто пиши, и я отвечу."
        )
        return True

    return False

# ---------- Основной цикл ----------
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
                    user_id = message.get("from", {}).get("id", 0)

                    # Имя: заданное пользователем или из Telegram
                    user_name = user_names.get(user_id) or message.get("from", {}).get("first_name", "незнакомка")

                    if not text or not chat_id:
                        continue

                    logger.info(f"Сообщение от {user_name} ({user_id}): {text[:50]}...")

                    # Проверяем, команда ли это
                    is_command = process_command(chat_id, user_id, text, user_name)

                    if not is_command:
                        send_chat_action(chat_id)
                        reply = ask_kobold(text, user_name)
                        send_message(chat_id, reply)

        except Exception as e:
            logger.error(f"Polling error: {e}")
            time.sleep(5)

# ---------- Старт ----------
if __name__ == "__main__":
    main()
