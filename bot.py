

import os
import time
import base64
import requests
import jwt
from flask import Flask, request, jsonify


app = Flask(__name__)

API_KEY_ID = os.getenv("COINBASE_API_KEY_ID")
PRIVATE_KEY_BASE64 = os.getenv("COINBASE_PRIVATE_KEY")

BASE_URL = "https://api.coinbase.com/api/v3/brokerage"
PRODUCT_ID = "SOL-USD"
TRADE_SIZE_USD = "5"  # SAFE TEST SIZE


def load_private_key():
    decoded_key = base64.b64decode(PRIVATE_KEY_BASE64)
    return serialization.load_der_private_key(
        decoded_key,
        password=None
    )


def generate_jwt():
    # Convert base64 key to PEM format
    pem_key = (
        "-----BEGIN PRIVATE KEY-----\n"
        + PRIVATE_KEY_BASE64
        + "\n-----END PRIVATE KEY-----"
    )

    payload = {
        "sub": API_KEY_ID,
        "iss": "cdp",
        "nbf": int(time.time()),
        "exp": int(time.time()) + 120,
        "aud": "https://api.coinbase.com"
    }

    token = jwt.encode(
        payload,
        pem_key,
        algorithm="ES256",
        headers={
            "kid": API_KEY_ID,
            "nonce": str(int(time.time()))
        }
    )

    return token


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
                "quote_size": TRADE_SIZE_USD
            }
        }
    }

    response = requests.post(url, headers=headers, json=body)

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




