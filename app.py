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

from telegram import ReplyKeyboardRemove  # добавь вверху рядом с другими импортами

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 1) сначала убираем старую клавиатуру
    await update.message.reply_text(
        "Обновляю меню…",
        reply_markup=ReplyKeyboardRemove()
    )

    # 2) затем показываем новую
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

    # 1) Обработка кнопок меню (роутинг)
    if user_message == "📄 Договоры":
        await update.message.reply_text(
            "Раздел: Договоры.\n\n"
            "Напиши одно из:\n"
            "1) Договор услуг\n"
            "2) Договор аренды\n"
            "3) Договор поставки\n\n"
            "И добавь 2 строки: кто стороны и что за услуга/товар."
        )
        return

    if user_message == "💰 Долги":
        await update.message.reply_text(
            "Раздел: Взыскание долгов.\n\n"
            "Ответь на 3 вопроса:\n"
            "1) Есть расписка/договор? (да/нет)\n"
            "2) Сумма и дата долга?\n"
            "3) Должник физлицо или ТОО/ИП?\n\n"
            "После этого дам пошаговый план + претензию."
        )
        return

    if user_message == "👔 Трудовые":
        await update.message.reply_text(
            "Раздел: Трудовые вопросы.\n\n"
            "Что нужно?\n"
            "1) Увольнение\n"
            "2) Зарплата/задержка\n"
            "3) Трудовой договор\n\n"
            "Кто вы: работник или работодатель? И город."
        )
        return

    if user_message == "⚖️ Суд":
        await update.message.reply_text(
            "Раздел: Суд.\n\n"
            "Укажи:\n"
            "1) Суть спора (кратко)\n"
            "2) Сумма/требование\n"
            "3) Есть ли доказательства/документы\n\n"
            "Дам шаги: подсудность, госпошлина, порядок подачи."
        )
        return

    if user_message == "📥 Шаблоны":
        await update.message.reply_text(
            "Шаблоны (РК):\n"
            "1) Договор услуг\n"
            "2) Договор аренды\n"
            "3) Договор поставки\n"
            "4) Претензия о взыскании долга\n"
            "5) Иск о взыскании долга\n\n"
            "Напиши номер шаблона — пришлю структуру и что нужно заполнить."
        )
        return

    # 2) Всё остальное — обычный вопрос к ИИ
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
        await update.message.reply_text("Произошла техническая ошибка. Попробуйте позже.")
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
