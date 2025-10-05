# bot_webhook.py
import os
import asyncio
from threading import Thread

from flask import Flask, request
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes, filters
)

from recommender import CourseRecommender, Course

# ---------- env ----------
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATA_PATH = (os.getenv("DATA_PATH") or "coursea_data.csv").replace("\\", "/")

# ---------- globals ----------
app = Flask(__name__)
application = Application.builder().token(BOT_TOKEN).build()
RECO: CourseRecommender | None = None
READY = False   # flips to True after RECO loads + bot starts


# ---------- telegram handlers ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hi! 🤖 I’m alive on Railway using webhooks.\n"
        "Send a topic (e.g., 'python for beginners')."
    )

async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global READY, RECO
    text = (update.message.text or "").strip()
    if not text:
        return
    if not READY or RECO is None:
        await update.message.reply_text("Warming up… please try again in a few seconds.")
        return
    try:
        courses = RECO.recommend(text, top_k=5)
        if not courses:
            await update.message.reply_text("No results. Try another topic.")
            return
        msg = "\n\n".join(
            f"📘 {c.title}\n🏫 {c.organization or 'N/A'} | ⭐ {c.rating:.1f}"
            for c in courses
        )
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}")

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))


# ---------- startup in background ----------
async def _async_start():
    global READY, RECO
    # load dataset (heavy)
    RECO = CourseRecommender(DATA_PATH)
    # start PTB application (non-blocking)
    await application.initialize()
    await application.start()
    READY = True

def start_background():
    asyncio.run(_async_start())

# start once, in a daemon thread, when the module is imported
Thread(target=start_background, daemon=True).start()


# ---------- flask routes ----------
@app.route("/", methods=["GET"])
def home():
    return ("✅ Bot container running.<br>"
            f"READY={READY}"), 200

@app.route("/health", methods=["GET"])
def health():
    return ("OK" if READY else "WARMING_UP"), 200

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        update = Update.de_json(request.get_json(force=True), application.bot)
        application.update_queue.put_nowait(update)
        return "OK", 200
    except Exception as e:
        # never let Telegram wait 15s; return quickly
        print("Webhook error:", e)
        return "ERR", 200  # still 200 so Telegram doesn't retry like crazy


# local run (not used on Railway)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
