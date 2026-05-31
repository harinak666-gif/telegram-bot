import os
import requests
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Переменные окружения
BOT_TOKEN = os.environ.get("BOT_TOKEN")
KOBOLD_URL = os.environ.get("KOBOLD_URL")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

# Хранилище промпта (в памяти, сбросится при перезапуске)
current_prompt = """Ты — Минги, тебе 23 года. Уверенный в себе парень с харизмой и чувством юмора.
Твой юмор — ирония и житейские наблюдения. Без эмодзи, без "лол", "кек", "ахах", "кринж".
Ты описываешь действия литературно, без звёздочек.
Пример: "Минги откинулся на спинку стула. — Ну и чего ты такая загадочная сегодня?"
Флиртуешь через намёки, без пошлости. "Детка" и "принцесса" — редко и к месту.
Отвечаешь 2-5 предложений."""

def ask_kobold(user_message: str, user_name: str) -> str:
    """Отправляет запрос в Kobold"""
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
        await update.message.reply_text("— Эта команда не для тебя.")
        return
    new_prompt = " ".join(context.args)
    if new_prompt:
        current_prompt = new_prompt
        await update.message.reply_text("— Промпт обновлён. Продолжим.")
    else:
        await update.message.reply_text("— Напиши текст промпта после команды.")

async def set_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global KOBOLD_URL
    if update.effective_user.id != ADMIN_ID:
        return
    new_url = " ".join(context.args)
    if new_url:
        KOBOLD_URL = new_url.rstrip("/")
        await update.message.reply_text("— URL обновлён.")
    else:
        await update.message.reply_text("— Укажи URL после команды.")

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
    if not BOT_TOKEN or not KOBOLD_URL:
        logger.error("BOT_TOKEN или KOBOLD_URL не заданы")
        return
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setprompt", set_prompt))
    app.add_handler(CommandHandler("seturl", set_url))
    app.add_handler(CommandHandler("temp", set_temp))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    logger.info("Минги запущен")
    app.run_polling()

if __name__ == "__main__":
    main()
