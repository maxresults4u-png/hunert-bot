import os
import time
import re
import requests
import jwt
from flask import Flask, request, jsonify

app = Flask(__name__)

API_KEY_ID = os.getenv("COINBASE_API_KEY_ID")
PRIVATE_KEY_RAW = os.getenv("COINBASE_PRIVATE_KEY") 

BASE_URL = "https://api.coinbase.com"
PRODUCT_ID = "SOL-USD"
TRADE_SIZE_USD = "5"

def generate_jwt():
    if not PRIVATE_KEY_RAW:
        raise ValueError("COINBASE_PRIVATE_KEY_MISSING")

    clean_key = re.sub(r'[^a-zA-Z0-9+/=]', '', PRIVATE_KEY_RAW)
    
    pem_key = (
        "-----BEGIN EC PRIVATE KEY-----\n"
        f"{clean_key}\n"
        "-----END EC PRIVATE KEY-----\n"
    )

    payload = {
        "sub": API_KEY_ID,
        "iss": "coinbase-cloud",
        "nbf": int(time.time()),
        "exp": int(time.time()) + 120,
        "aud": ["retail_rest_api_proxy"],
    }

    token = jwt.encode(
        payload,
        pem_key.encode("utf-8"),
        algorithm="ES256",
        headers={
            "kid": API_KEY_ID,
            "nonce": os.urandom(16).hex(),
            "typ": "JWT"
        }
    )
    return token

def place_market_buy():
    url = f"{BASE_URL}/orders"
    try:
        token = generate_jwt()
    except Exception as e:
        return {"error": f"JWT_FAILED: {str(e)}"}

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

    action = data.get("action")
    if action == "LONG":
        result = place_market_buy()
        return jsonify(result)

    return jsonify({"status": "ignored", "action": action})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
