from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
import json
import re
import os  # Added to support environment variables

BOT_TOKEN = os.getenv("8567964192:AAE1Obm13mBxfEIX9A3_4i4l_QwDZAH3yJA")
CHANNEL_ID = os.getenv("@mitconfession")
ADMIN_IDS = [int(os.getenv("ADMIN_ID", "5878466126"))]  # Optional: set via env
PENDING_FILE = "pending_confessions.json"
COUNTER_FILE = "confession_counter.txt"

def get_next_confession_id():
    try:
        with open(COUNTER_FILE, "r") as f:
            current = int(f.read())
    except FileNotFoundError:
        current = 100
    with open(COUNTER_FILE, "w") as f:
        f.write(str(current + 1))
    return current

def load_pending():
    try:
        with open(PENDING_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_pending(data):
    with open(PENDING_FILE, "w") as f:
        json.dump(data, f)

async def handle_confession(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    match = re.match(r"#(\d+)\s+(.+)", text)
    
    if match:
        confession_id = match.group(1)
        comment = match.group(2)
        await context.bot.send_message(chat_id=CHANNEL_ID, text=f"💬 Comment on #{confession_id}:\n{comment}")
        await update.message.reply_text("✅ Your comment has been posted anonymously.")
    else:
        confession_id = get_next_confession_id()
        pending = load_pending()
        pending[str(confession_id)] = text
        save_pending(pending)
        await update.message.reply_text(f"🕒 Confession #{confession_id} submitted for review.")

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    if not context.args:
        await update.message.reply_text("❗ Usage: /approve <confession_id>")
        return
    confession_id = context.args[0]
    pending = load_pending()
    if confession_id in pending:
        await context.bot.send_message(chat_id=CHANNEL_ID, text=f"📢 Anonymous Confession #{confession_id}:\n{pending[confession_id]}")
        del pending[confession_id]
        save_pending(pending)
        await update.message.reply_text(f"✅ Confession #{confession_id} approved and posted.")
    else:
        await update.message.reply_text("❌ Confession not found.")

async def reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    if not context.args:
        await update.message.reply_text("❗ Usage: /reject <confession_id>")
        return
    confession_id = context.args[0]
    pending = load_pending()
    if confession_id in pending:
        del pending[confession_id]
        save_pending(pending)
        await update.message.reply_text(f"🗑️ Confession #{confession_id} rejected.")
    else:
        await update.message.reply_text("❌ Confession not found.")

# Bot setup
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_confession))
app.add_handler(CommandHandler("approve", approve))
app.add_handler(CommandHandler("reject", reject))

# ✅ Webhook mode for Railway
PORT = int(os.environ.get('PORT', 8443))
app.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    url_path=BOT_TOKEN,
    webhook_url=f"https://mit-confession-bot.up.railway.app/{BOT_TOKEN}"
)
