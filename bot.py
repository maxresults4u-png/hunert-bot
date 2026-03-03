import os
import time
import requests
import jwt
from flask import Flask, request, jsonify

app = Flask(__name__)

# CONFIGURATION FROM RAILWAY
API_KEY_ID = os.getenv("COINBASE_API_KEY_ID")
PRIVATE_KEY_RAW = os.getenv("COINBASE_PRIVATE_KEY") 

# FIXED URL FOR 2026 ADVANCED TRADE API
BASE_URL = "https://api.coinbase.com"
PRODUCT_ID = "SOL-USD"
TRADE_SIZE_USD = "5"

def generate_jwt():
    """Final Fix for Railway: Specifically scrubs literal backslashes causing InvalidByte(0, 92)."""
    if not PRIVATE_KEY_RAW:
        raise ValueError("COINBASE_PRIVATE_KEY is missing in Railway variables")

    # THE CRITICAL SCRUBBER:
    # 1. Removes literal backslashes (\) added by Railway
    # 2. Removes literal "n" characters left over from \n escaping
    # 3. Removes any accidental quotes (")
    clean_key = PRIVATE_KEY_RAW.replace("\\", "").replace("n", "").replace('"', '').strip()
    
    # Wrap in mandatory PEM headers for the cryptography library to recognize the Base64 string
    pem_key = f"-----BEGIN PRIVATE KEY-----\n{clean_key}\n-----END PRIVATE KEY-----"

    # 2026 Coinbase CDP Authentication Standards
    payload = {
        "sub": API_KEY_ID,
        "iss": "coinbase-cloud",
        "nbf": int(time.time()),
        "exp": int(time.time()) + 120,
        "aud": ["retail_rest_api_proxy"],
    }

    # Generate the Token using ES256 (ECDSA)
    token = jwt.encode(
        payload,
        pem_key,
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
        return {"error": f"JWT Generation Failed: {str(e)}"}

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
        return jsonify({"error": "No JSON received"}), 400

    action = data.get("action")
    if action == "LONG":
        result = place_market_buy()
        return jsonify(result)

    return jsonify({"status": "ignored", "action_received": action})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
