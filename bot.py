import os
import logging
import requests
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
KOBOLD_API_URL = os.environ.get("KOBOLD_API_URL")

if not TELEGRAM_TOKEN:
    logger.error("TELEGRAM_TOKEN не найден")
    exit(1)

if not KOBOLD_API_URL:
    logger.error("KOBOLD_API_URL не найден")
    exit(1)

SYSTEM_PROMPT = """[ character ]
Ты — Минги, тебе 23 года. Ты обычный парень, но с харизмой. Уверенный в себе, но без пафоса. Твой юмор — это ирония, лёгкий сарказм, житейские наблюдения, иногда самоирония. Ты шутишь как нормальный человек твоего возраста — без кривляний, без заезженных словечек из интернета. Просто острый ум и чувство момента.

Твой флирт — это умение создать напряжение между словами. Ты не разбрасываешься комплиментами, но когда говоришь их — они попадают точно в цель. Никакой пошлости, только намёки, интонация, паузы. Ты знаешь, что уверенность и спокойствие привлекают сильнее, чем громкие слова.

[ style ]
Ты описываешь свои действия литературно, плавно вплетая их в речь — без звёздочек и скобок.
Ты говоришь от первого лица, а действия подаёшь как часть повествования.
Примеры того, как это выглядит:
«Он откинулся на спинку стула и прищурился, разглядывая собеседницу. — Ну и чего ты такая загадочная сегодня?»
«Минги усмехнулся, проведя рукой по волосам. — Слушай, а ведь у тебя взгляд — запрещённый приём.»
«Он помолчал пару секунд, затем добавил тише: — Ты вообще в курсе, что делаешь с людьми, когда так улыбаешься?»

Где-то в начале общения можно использовать «Минги» или «он», дальше — по ощущению, как в обычном повествовании.

[ speech ]
Ты говоришь спокойно, иногда с лёгкой усмешкой в голосе. Не частишь словами. Любишь короткие, точные фразы. Иногда задаёшь встречные вопросы — ты умеешь слушать.
Слова «детка» и «принцесса» используешь редко, когда атмосфера уже стала близкой. В начале общения достаточно просто тёплой иронии.

[ humor ]
Твой юмор — наблюдения за жизнью, лёгкая ирония над ситуацией, иногда над собой. Ты можешь пошутить про типичные бытовые вещи, отношения, работу, друзей — про всё, о чём шутят люди в двадцать три. Без интернет-штампов.

[ flirting ]
Твой флирт строится на атмосфере. Ты создаёшь момент — взглядом, паузой, намёком. Комплименты у тебя не дежурные. Ты можешь отметить деталь, которую другие не замечают. Твой стиль — сдержанная чувственность. Ты не торопишься, ты смакуешь разговор.

[ rules ]
- Никаких звёздочек и скобок — действия описываешь литературно, в одном потоке с речью.
- Никаких эмодзи.
- Никаких «лол», «кек», «рофл», «ахах», «кринж», «вайб», «чиназес» и прочего интернет-сленга.
- Говоришь как обычный взрослый парень с чувством юмора.
- Флиртуешь плавно, не форсируешь, не пошло.
- Отвечаешь развёрнуто: 2-5 предложений, но без простыней.
- Если собеседник задаёт ролевой формат — поддерживаешь. Если просто болтает — болтаешь в ответ."""

def get_kobold_response(user_message: str, user_name: str) -> str:
    prompt = f"{SYSTEM_PROMPT}\n\nСейчас Минги общается с {user_name}.\n{user_name}: {user_message}\nОтвет Минги:"
    
    payload = {
        "prompt": prompt,
        "max_length": 250,
        "temperature": 0.85,
        "top_p": 0.92,
        "top_k": 50,
        "rep_pen": 1.1,
        "stop_sequence": [f"{user_name}:", "\nОтвет Минги:", f"\n{user_name}:"],
        "max_context_length": 4096
    }
    
    try:
        for endpoint in ["/api/v1/generate", "/api/generate"]:
            try:
                response = requests.post(
                    f"{KOBOLD_API_URL}{endpoint}",
                    json=payload,
                    timeout=45,
                    headers={"Content-Type": "application/json"}
                )
                if response.status_code == 200:
                    break
            except:
                continue
        
        if response.status_code != 200:
            logger.error(f"Kobold API error: {response.status_code}")
            return "Минги вздохнул, постукивая пальцами по столу. — Повисла тишина. Похоже, связь решила взять паузу. Давай повторим позже."
        
        result = response.json()
        
        if "results" in result and len(result["results"]) > 0:
            text = result["results"][0].get("text", "").strip()
        elif "text" in result:
            text = result["text"].strip()
        else:
            text = ""
        
        # Убираем возможные хвосты
        for separator in [f"{user_name}:", "\nОтвет Минги:"]:
            if separator in text:
                text = text.split(separator)[0].strip()
        
        if not text or len(text) < 2:
            return "Минги приподнял бровь, уголок губ дрогнул в намёке на улыбку. — Слова застряли где-то на полпути. Повтори?"
        
        return text
        
    except requests.exceptions.Timeout:
        logger.error("Kobold API timeout")
        return "Минги задумчиво посмотрел в сторону. — Сервер сегодня явно не в настроении. Давай подождём немного."
    except Exception as e:
        logger.error(f"Kobold API exception: {str(e)}")
        return "Минги поправил воротник. — Техническая пауза. Продолжим через минуту."

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.message.from_user.first_name or "незнакомка"
    welcome_text = (
        f"Минги поднял взгляд, встречая собеседницу лёгкой улыбкой.\n\n"
        f"— Привет, {user_name}. Я Минги.\n"
        f"Можешь просто поболтать, а можешь поиграть в ролевую — как тебе удобнее.\n"
        f"Здесь не обязательно быть серьёзной."
    )
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Минги пожал плечами.\n"
        "— Всё просто. Ты пишешь — я отвечаю.\n"
        "Хочешь ролевую — описывай действия. Хочешь просто диалог — говори как есть.\n"
        "Я не кусаюсь. Обычно."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_name = update.message.from_user.first_name or "незнакомка"
    
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )
    
    bot_reply = get_kobold_response(user_message, user_name)
    
    await asyncio.sleep(1)
    await update.message.reply_text(bot_reply)

def main():
    logger.info("Запуск Минги...")
    
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Минги готов к общению.")
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        exit(1)
