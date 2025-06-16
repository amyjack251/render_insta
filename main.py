import os
import re
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

SESSION_FILE = "sessionid.txt"

# Load session ID if exists
def load_session():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as f:
            return f.read().strip()
    return None

# Save session ID
def save_session(sessionid):
    with open(SESSION_FILE, "w") as f:
        f.write(sessionid)

# Delete session ID
def delete_session():
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)

BOT_TOKEN = os.getenv("BOT_TOKEN")
sessionid = load_session()

URL_REGEX = r"(https?://[\w./?=&%-]+(?:instagram\.com|youtu\.be|youtube\.com|tiktok\.com)[^\s]*)"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    match = re.search(URL_REGEX, text)
    if not match:
        await update.message.reply_text("❌ No supported link found.")
        return

    url = match.group(1)
    await update.message.reply_text("⏳ Downloading media...")

    ydl_opts = {
        'outtmpl': 'downloads/%(title).70s.%(ext)s',
        'format': 'best',
        'quiet': True,
    }

    # Add sessionid cookie if needed
    if 'instagram.com' in url and sessionid:
        ydl_opts['cookiefile'] = SESSION_FILE
        with open(SESSION_FILE, 'w') as f:
            f.write(f"sessionid={sessionid}")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            filename = ydl.prepare_filename(info)
            ydl.download([url])

        if os.path.exists(filename):
            await update.message.reply_video(video=open(filename, 'rb'))
            os.remove(filename)
        else:
            await update.message.reply_text("⚠️ Downloaded but file not found.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def set_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        new_id = context.args[0].strip()
        save_session(new_id)
        global sessionid
        sessionid = new_id
        await update.message.reply_text("✅ Session ID saved.")
    else:
        await update.message.reply_text("⚠️ Usage: /session SESSIONID")

async def delete_session_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    delete_session()
    global sessionid
    sessionid = None
    await update.message.reply_text("❌ Session ID deleted.")

# ✅ Entry point
if name == "main":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("session", set_session))
    app.add_handler(CommandHandler("delete", delete_session_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot is running...")
    app.run_polling()
