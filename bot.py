import os
import time
import requests
import jwt
from flask import Flask, request, jsonify

app = Flask(__name__)

# CONFIGURATION
API_KEY_ID = os.getenv("COINBASE_API_KEY_ID")
# This should be the raw string (the one starting with Wek... and ending with ==)
PRIVATE_KEY_RAW = os.getenv("COINBASE_PRIVATE_KEY")

BASE_URL = "https://api.coinbase.com"
PRODUCT_ID = "SOL-USD"
TRADE_SIZE_USD = "5"

def generate_jwt():
    """Generates a valid Coinbase CDP JWT token."""
    # Ensure the key is wrapped correctly for the cryptography library
    # We use .strip() to catch any accidental spaces from Railway's UI
    clean_key = PRIVATE_KEY_RAW.strip().replace("\\n", "\n")
    
    # If the key doesn't already have headers, add them
    if "-----BEGIN" not in clean_key:
        pem_key = f"-----BEGIN PRIVATE KEY-----\n{clean_key}\n-----END PRIVATE KEY-----"
    else:
        pem_key = clean_key

    payload = {
        "sub": API_KEY_ID,
        "iss": "coinbase-cloud",
        "nbf": int(time.time()),
        "exp": int(time.time()) + 120,
        "aud": ["retail_rest_api_proxy"],
    }

    # PyJWT handles the ASN.1 parsing internally
    token = jwt.encode(
        payload,
        pem_key,
        algorithm="ES256",
        headers={
            "kid": API_KEY_ID,
            "nonce": os.urandom(16).hex() # More secure nonce for 2026
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
    return {
        "status_code": response.status_code,
        "response": response.json() if response.status_code == 200 else response.text
    }

@app.route("/", methods=["POST"])
def webhook():
    # force=True handles cases where Content-Type header isn't set to json
    data = request.get_json(force=True)

    if not data:
        return jsonify({"error": "No JSON received"}), 400

    action = data.get("action")

    if action == "LONG":
        result = place_market_buy()
        return jsonify(result)

    return jsonify({"status": "no action", "received": action})

if __name__ == "__main__":
    # Railway provides the PORT environment variable
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)









