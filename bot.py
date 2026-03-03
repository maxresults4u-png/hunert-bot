import os
import time
import json
import hmac
import hashlib
import base64
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

API_KEY_ID = os.getenv("COINBASE_API_KEY_ID")
API_SECRET = os.getenv("COINBASE_API_SECRET")

BASE_URL = "https://api.coinbase.com"
PRODUCT_ID = "SOL-USD"
TRADE_SIZE_USD = "5"


def sign_request(timestamp, method, request_path, body):
    message = f"{timestamp}{method}{request_path}{body}"
    signature = hmac.new(
        API_SECRET.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    ).digest()
    return base64.b64encode(signature).decode()


def place_market_buy():
    method = "POST"
    request_path = "/api/v3/brokerage/orders"
    url = BASE_URL + request_path

    body = {
        "client_order_id": str(int(time.time())),
        "product_id": PRODUCT_ID,
        "side": "BUY",
        "order_configuration": {
            "market_market_ioc": {
                "quote_size": TRADE_SIZE_USD
            }
        }
    }

    body_json = json.dumps(body)
    timestamp = str(int(time.time()))

    signature = sign_request(timestamp, method, request_path, body_json)

    headers = {
        "CB-ACCESS-KEY": API_KEY_ID,
        "CB-ACCESS-SIGN": signature,
        "CB-ACCESS-TIMESTAMP": timestamp,
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, data=body_json)

    try:
        return {
            "status_code": response.status_code,
            "response": response.json()
        }
    except:
        return {
            "status_code": response.status_code,
            "response": response.text
        }


@app.route("/", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    if not data:
        return jsonify({"error": "NO_JSON"}), 400

    if data.get("action") == "LONG":
        return jsonify(place_market_buy())

    return jsonify({"status": "ignored"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
