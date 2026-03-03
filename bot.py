import os
import time
import requests
import jwt
from flask import Flask, request, jsonify

app = Flask(__name__)

# CONFIGURATION FROM RAILWAY
API_KEY_ID = os.getenv("COINBASE_API_KEY_ID")
PRIVATE_KEY_RAW = os.getenv("COINBASE_PRIVATE_KEY") # The raw string starting with Wek...

BASE_URL = "https://api.api.coinbase.com"
PRODUCT_ID = "SOL-USD"
TRADE_SIZE_USD = "5"

def generate_jwt():
    """Generates a Coinbase CDP JWT token with strict 2026 formatting."""
    if not PRIVATE_KEY_RAW:
        raise ValueError("COINBASE_PRIVATE_KEY is missing in Railway variables")

    # FIX: The "InvalidByte(0, 92)" error is caused by literal backslashes (\).
    # This line converts literal "\n" text back into real line breaks.
    clean_key = PRIVATE_KEY_RAW.replace("\\n", "\n").strip()
    
    # Ensure the key is wrapped in the PEM headers required by the 'cryptography' library
    if "-----BEGIN" not in clean_key:
        pem_key = f"-----BEGIN PRIVATE KEY-----\n{clean_key}\n-----END PRIVATE KEY-----"
    else:
        pem_key = clean_key

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
    
    # Return detailed response for debugging
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
    # force=True handles TradingView's default content-type
    data = request.get_json(force=True)

    if not data:
        return jsonify({"error": "No JSON received"}), 400

    # TradingView Alert Message: {"action": "LONG"}
    action = data.get("action")

    if action == "LONG":
        result = place_market_buy()
        return jsonify(result)

    return jsonify({"status": "ignored", "action_received": action})

if __name__ == "__main__":
    # Railway dynamic port binding
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
    
