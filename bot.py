import os
from telegram.ext import Updater, CommandHandler

print("Hunter bot is starting...")

# Get token from Railway Variables
TOKEN = "8744376444:AAEsDqM3eYXBbhYGjDn28rlELWPGgt0W3HQ"

if not TOKEN:
    raise Exception("TELEGRAM_BOT_TOKEN is missing from Railway variables")

print("TOKEN loaded successfully")

# Commands
def start(update, context):
    update.message.reply_text("Hunter bot is live 🚀")

def hello(update, context):
    update.message.reply_text("Bot is running on Railway ✅")

# Start bot
def main():
    updater = Updater(token=TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("hello", hello))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()

