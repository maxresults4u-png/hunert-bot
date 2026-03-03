import os
import time
import base64
import requests
import jwt
from flask import Flask, request, jsonify
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

app = Flask(__name__)

API_KEY_ID = os.getenv("COINBASE_API_KEY_ID")
PRIVATE_KEY_BASE64 = os.getenv("COINBASE_PRIVATE_KEY")
