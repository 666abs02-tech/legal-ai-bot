import os
import asyncio
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters,
)
from openai import OpenAI

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

if not TELEGRAM_TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN не установлен")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY не установлен")

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = (
    "Ты юридический помощник по законодательству Республики Казахстан.\n"
    "Отвечай структурировано:\n"
    "1) Кратко по сути.\n"
    "2) Пошаговые действия.\n"
    "3) Необходимые документы.\n"
    "4) Возможные риски.\n\n"
    "В конце всегда добавляй: "
    "Информация носит справочный характер и не является юридической консультацией."
)

menu_keyboard = ReplyKeyboardMarkup(
    [
        ["📄 Договоры", "💰 Долги"],
        ["👔 Трудовые", "⚖️ Суд"],
        ["📥 Шаблоны"]
    ],
    resize_keyboard=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Здравствуйте.\n\n"
        "Я AI-юридический помощник по законодательству РК.\n\n"
        "Выберите раздел ниже или задайте вопрос.",
        reply_markup=menu_keyboard
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = (update.message.text or "").strip()
    if not user_message:
        return

    try:
        def ask_openai():
            return client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
            )

        response = await asyncio.to_thread(ask_openai)
        answer = response.choices[0].message.content.strip()

        if len(answer) > 3500:
            answer = answer[:3500]

        await update.message.reply_text(answer)

    except Exception:
        await update.message.reply_text(
            "Произошла техническая ошибка. Попробуйте позже."
        )

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if _name_ == "_main_":
    main()
