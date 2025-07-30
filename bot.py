import logging
import json
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

# Настройка логов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка автоответов
with open("azimuse_auto_replies.json", "r", encoding="utf-8") as file:
    auto_replies = json.load(file)

# Храним выбранный язык
user_language = {}

# /start — выбор языка
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [["🇷🇺 Русский", "🇬🇧 English"]]
    await update.message.reply_text(
        "Добро пожаловать в AZIMUSE!\nWelcome to AZIMUSE!\n\nПожалуйста, выберите язык / Please choose a language:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
    )

# Универсальный обработчик сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    text = update.message.text

    # 1. Установка языка, если ещё не выбран
    if chat_id not in user_language:
        if "Русский" in text:
            user_language[chat_id] = "RU"
        elif "English" in text:
            user_language[chat_id] = "EN"
        else:
            await update.message.reply_text("Пожалуйста, выберите язык командой /start.")
            return

        lang = user_language[chat_id]
        questions = [KeyboardButton(q["question"]) for q in auto_replies[lang]]
        questions.append(KeyboardButton("📝 Оставить отзыв"))
        questions.append(KeyboardButton("❓ Другое / Contact manufacturer"))

        reply_markup = ReplyKeyboardMarkup(
            [[q] for q in questions],
            resize_keyboard=True
        )

        await update.message.reply_text(
            "Выберите вопрос / Please choose a question:",
            reply_markup=reply_markup
        )
        return

    # 2. Обработка запроса после выбора языка
    lang = user_language[chat_id]

    # Нажали "Другое"
    if text == "❓ Другое / Contact manufacturer":
        await update.message.reply_text(
            "Пожалуйста, опишите свой вопрос. Мы ответим вам в ближайшее время." if lang == "RU"
            else "Please describe your question. We will get back to you soon."
        )
        context.user_data["awaiting_question"] = True
        return

    # Нажали "Оставить отзыв"
    if text == "📝 Оставить отзыв":
        await update.message.reply_text(
            "Пожалуйста, напишите свой отзыв. Мы обязательно его учтем!" if lang == "RU"
            else "Please write your review. We will definitely take it into account!"
        )
        context.user_data["awaiting_review"] = True
        return

    # Обработка сообщения-отзыва
    if context.user_data.get("awaiting_review"):
        context.user_data["awaiting_review"] = False

        admin_message = f"📝 Новый отзыв от пользователя @{update.message.from_user.username or 'Без имени'}:\n\n{text}\nChat ID: {chat_id}"
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_message)

        await update.message.reply_text(
            "Спасибо за ваш отзыв! Мы его внимательно рассмотрим." if lang == "RU"
            else "Thank you for your review! We will carefully consider it."
        )
        return

    # Обработка сообщения с вопросом, если ожидали вопрос
    if context.user_data.get("awaiting_question"):
        context.user_data["awaiting_question"] = False

        admin_message = f"📩 Сообщение от пользователя @{update.message.from_user.username or 'Без имени'}:\n\n{text}\nChat ID: {chat_id}"
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_message)

        await update.message.reply_text(
            "Ваш вопрос отправлен. Мы свяжемся с вами в ближайшее время." if lang == "RU"
            else "Your question has been sent. We will contact you soon."
        )
        return

    # Поиск автоответа
    for item in auto_replies[lang]:
        if item["question"].lower() == text.lower():
            await update.message.reply_text(item["answer"])
            return

    # Если вопрос не найден
    await update.message.reply_text(
        "Ответ не найден. Пожалуйста, выберите 'Другое / Contact manufacturer' и опишите свой вопрос." if lang == "RU"
        else "Answer not found. Please choose 'Other / Contact manufacturer' and describe your question."
    )

# Запуск бота
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("🤖 AZIMUSE бот запущен и работает...")
    app.run_polling()