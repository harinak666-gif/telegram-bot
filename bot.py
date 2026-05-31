import os
import sys
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Проверка версии Python
if sys.version_info < (3, 8):
    raise RuntimeError("Требуется Python 3.8+")

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

temperature = 0.85

def ask_kobold(user_message: str, user_name: str) -> str:
    full_prompt = f"{current_prompt}\n\n{user_name}: {user_message}\nМинги:"
    payload = {
        "prompt": full_prompt,
        "max_length": 200,
        "temperature": temperature,
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
            return text if text else "Минги замолчал, подбирая слова. — Прости, задумался."
        else:
            logger.error(f"Kobold ответил: {resp.status_code}")
            return "Минги постучал пальцем по столу. — Похоже, связь барахлит."
    except Exception as e:
        logger.error(f"Ошибка Kobold: {e}")
        return "Минги вздохнул. — Сервер ушёл в астрал. Давай позже."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Минги поднял взгляд и улыбнулся.\n— Привет. Я здесь. Можешь просто болтать или играть в ролевую — как хочешь."
    )

async def set_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_prompt
    if update.effective_user.id != ADMIN_ID:
        return
    new_prompt = " ".join(context.args)
    if new_prompt:
        current_prompt = new_prompt
        await update.message.reply_text("— Промпт обновлён.")
    else:
        await update.message.reply_text("— Напиши текст после команды.")

async def set_temp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global temperature
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        temperature = float(context.args[0])
        await update.message.reply_text(f"— Температура: {temperature}")
    except:
        await update.message.reply_text("— Пример: /temp 0.9")

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text
    user_name = update.message.from_user.first_name or "незнакомка"
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    reply = ask_kobold(user_msg, user_name)
    await update.message.reply_text(reply)

def main():
    logger.info("Запуск Минги...")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setprompt", set_prompt))
    app.add_handler(CommandHandler("temp", set_temp))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    logger.info("Минги запущен")
    app.run_polling()

if __name__ == "__main__":
    main()
