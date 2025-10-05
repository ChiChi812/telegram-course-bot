from flask import Flask, request
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters
)
from dotenv import load_dotenv
import os
from recommender import CourseRecommender, Course

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATA_PATH = (os.getenv("DATA_PATH", "C:/Users/Lenovo/OneDrive/Desktop/TelegramCourseBot/coursea_data.csv"))

app = Flask(__name__)
application = Application.builder().token(BOT_TOKEN).build()
RECO = CourseRecommender(DATA_PATH)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi! I’m alive on Render using webhooks 🚀")

async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    if not text:
        return
    courses = RECO.recommend(text, top_k=5)
    msg = "\n\n".join([c.title for c in courses])
    await update.message.reply_text(f"Top matches:\n{msg}")

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))

@app.route("/")
def home():
    return "Bot is alive!", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    """Receive updates from Telegram."""
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "OK", 200
