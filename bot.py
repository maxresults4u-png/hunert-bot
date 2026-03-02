from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# ---------------------------------
# TELEGRAM SETTINGS
# ---------------------------------
TOKEN = "8744376444:AAEsDqM3eYXBbhYGjDn28rlELWPGgt0W3HQ"
CHAT_ID = 8781402847   # <-- replace with your chat ID

BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

# ---------------------------------
# Send message to Telegram
# ---------------------------------
def send_message(chat_id, text):
    url = f"{BASE_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    r = requests.post(url, json=payload)
    print("Telegram response:", r.text)

# ---------------------------------
# Health check (browser test)
# ---------------------------------
@app.route("/", methods=["GET"])
def home():
    return "✅ Bot is running!"

# ---------------------------------
# Telegram + TradingView webhook
# ---------------------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("Received data:", data)

    # ----- Telegram message -----
    if data and "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        send_message(chat_id, f"✅ Bot received: {text}")

    # ----- TradingView alert -----
    elif data and "action" in data:
        symbol = data.get("symbol", "Unknown")
        action = data.get("action", "ALERT")
        price = data.get("price", "N/A")

        alert_msg = f"🚨 {action} {symbol} at {price}"
        send_message(CHAT_ID, alert_msg)

    return jsonify({"status": "success"}), 200

# ---------------------------------
# Start Flask server
# ---------------------------------
if __name__ == "__main__":
    print("Hunter bot is running...")
    
    from telegram.ext import Updater, CommandHandler
    
    import os
    
    TOKEN = os.getenv("8744376444:AAEsDqM3eYXBbhYGjDn28rlELWPGgt0W3HQ")
    
    updater = Updater(TOKEN, use_context=True)
    
    dp = updater.dispatcher
    
    def start(update, context):
        update.message.reply_text("Hunter bot is live 🚀")
    
    dp.add_handler(CommandHandler("start", start))
    
    updater.start_polling()
    updater.idle()
