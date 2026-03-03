import os
import time
import requests
import jwt
from flask import Flask, request, jsonify

app = Flask(__name__)

API_KEY = os.getenv("COINBASE_API_KEY")
API_SECRET = os.getenv("COINBASE_API_SECRET")

print("API_KEY VALUE:", API_KEY)

BASE_URL = "https://api.coinbase.com/api/v3/brokerage"
PRODUCT_ID = "SOL-USD"
TRADE_SIZE_USD = 5  # SAFE TEST SIZE


def generate_jwt():
    payload = {
        "iss": API_KEY,
        "sub": API_KEY,
        "nbf": int(time.time()),
        "exp": int(time.time()) + 120,
        "aud": ["https://api.coinbase.com"]
    }
    return jwt.encode(payload, API_SECRET, algorithm="HS256")


def place_market_buy():
    url = f"{BASE_URL}/orders"
    token = generate_jwt()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    body = {
        "client_order_id": str(int(time.time())),
        "product_id": PRODUCT_ID,
        "side": "BUY",
        "order_configuration": {
            "market_market_ioc": {
                "quote_size": str(TRADE_SIZE_USD)
            }
        }
    }

    response = requests.post(url, headers=headers, json=body)

    print("Status Code:", response.status_code)
    print("Raw Response:", response.text)

    return {
        "status_code": response.status_code,
        "response": response.text
    }


@app.route("/", methods=["POST"])
def webhook():
    data = request.json
    action = data.get("action")

    if action == "LONG":
        result = place_market_buy()
        return jsonify(result)

    return jsonify({"status": "no action"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)


