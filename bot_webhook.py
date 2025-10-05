# bot_webhook.py
import os
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from dotenv import load_dotenv
from recommender import CourseRecommender, Course

# --- Load environment variables ---
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATA_PATH = (os.getenv("DATA_PATH") or "coursea_data.csv").replace("\\", "/")

# --- Initialize Telegram bot ---
app = Flask(__name__)
application = Application.builder().token(BOT_TOKEN).build()

# --- Load recommender dataset ---
RECO = CourseRecommender(DATA_PATH)


# --- Define handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hi! 🤖 I’m alive on Railway using webhooks!\n\n"
        "Type any topic (e.g., 'Python', 'Data Science') "
        "and I’ll recommend courses for you."
    )


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    if not text:
        return
    try:
        results = RECO.recommend(text, top_k=5)
        if not results:
            await update.message.reply_text("No results found, try another topic.")
            return

        msg = "\n\n".join(
            f"📘 {c.title}\n🏫 {c.organization or 'N/A'} | ⭐ {c.rating:.1f}"
            for c in results
        )
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error while processing: {e}")


# --- Register handlers ---
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))


# --- Flask endpoints ---
@app.route("/", methods=["GET"])
def home():
    return "✅ Bot is alive on Railway!", 200


@app.route("/webhook", methods=["POST"])
def webhook():
    """Receive Telegram updates."""
    try:
        update = Update.de_json(request.get_json(force=True), application.bot)
        application.update_queue.put_nowait(update)
    except Exception as e:
        print("Webhook error:", e)
        return "Error", 500
    return "OK", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
