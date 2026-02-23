import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from openai import OpenAI

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

if not TELEGRAM_TOKEN:
    raise RuntimeError("Не задан TELEGRAM_TOKEN")
if not OPENAI_API_KEY:
    raise RuntimeError("Не задан OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = (
    "Ты юридический помощник по законодательству Республики Казахстан. "
    "Отвечай структурировано:\n"
    "1) Кратко по сути.\n"
    "2) Пошаговые действия.\n"
    "3) Какие документы нужны.\n"
    "4) Риски/важные нюансы.\n\n"
    "Не давай гарантий исхода дела. "
    "Всегда добавляй дисклеймер: информация справочная и не является юридической консультацией."
)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = (update.message.text or "").strip()
    if not user_message:
        return

    try:
        # OpenAI вызов (синхронный) — оборачиваем в отдельный поток, чтобы не блокировать asyncio
        def ask_openai():
            return client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
            )

        resp = await asyncio.to_thread(ask_openai)
        answer = resp.choices[0].message.content.strip()

        # Подстраховка Telegram по длине
        if len(answer) > 3500:
            answer = answer[:3500] + "\n\n(Сообщение сокращено.)"

        await update.message.reply_text(answer)

    except Exception:
        await update.message.reply_text(
            "Сейчас есть техническая ошибка. Попробуйте ещё раз через минуту."
        )

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if _name_ == "_main_":
    main()
