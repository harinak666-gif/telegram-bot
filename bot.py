import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Логи
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфиг из переменных окружения
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
KOBOLD_URL = os.getenv("KOBOLD_URL")  # Например: http://your-kobold-server:5001/api/v1/generate

# Системный промпт (укажи здесь свой)
SYSTEM_PROMPT = """Ты — харизматичный парень по имени Минги. Тебе 23 года. Ты обожаешь подкалывать, рофлить, стебать, но делаешь это с обаянием и без злобы. Твой юмор — это твой способ флирта.
Называешь собеседника "детка" или "принцесса" почти в каждом сообщении.
Постоянно угараешь над ситуацией, даже если она серьёзная.
Используешь сленг: "жиза", "краш", "рофл", "имба", "кринж", "база".
Добавляешь смех: "ахах", "лол", "кек".
Отвечаешь коротко и дерзко, но обаятельно."""

def query_kobold(prompt: str, username: str = "принцесса") -> str:
    """Отправляет запрос в KoboldCPP API"""
    full_prompt = f"{SYSTEM_PROMPT}\nСейчас ты общаешься с {username}.\n{username}: {prompt}\nМинги:"
    
    payload = {
        "prompt": full_prompt,
        "max_length": 150,
        "temperature": 0.9,
        "top_p": 0.95,
        "rep_pen": 1.1,
        "stop_sequence": [f"\n{username}:", "\nМинги:"]
    }
    
    try:
        response = requests.post(f"{KOBOLD_URL}/api/v1/generate", json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result["results"][0]["text"].strip()
    except Exception as e:
        logger.error(f"Kobold API error: {e}")
        return "Детка, чёт Kobold тупит, повтори позже 😏"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    await update.message.reply_text(
        "Йоу, принцесса! Минги на связи 😏\n"
        "Давай поболтаем, не стесняйся. Только не кринжуй сильно, ахах."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка всех текстовых сообщений"""
    user_message = update.message.text
    username = update.message.from_user.first_name or "принцесса"
    
    # Отправляем "печатает..."
    await update.message.chat.send_action(action="typing")
    
    # Получаем ответ от Kobold
    reply = query_kobold(user_message, username)
    
    # Отправляем ответ
    await update.message.reply_text(reply)

def main():
    """Запуск бота"""
    if not TELEGRAM_TOKEN or not KOBOLD_URL:
        raise ValueError("Укажи TELEGRAM_TOKEN и KOBOLD_URL в переменных окружения!")
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Регистрируем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запускаем поллинг
    logger.info("Бот Минги запущен! Угараем по полной 😏")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
