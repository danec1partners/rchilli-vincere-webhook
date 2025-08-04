
import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

@app.route('/', methods=['GET'])
def home():
    return "✅ RChilli to Vincere webhook is alive (safe mode)"

@app.route('/', methods=['POST'])
def webhook():
    try:
        print("📥 Incoming POST request")
        print("🔍 Content-Type:", request.headers.get('Content-Type', ''))

        raw_bytes = request.data
        decoded_text = raw_bytes.decode('utf-8', errors='replace')

        print("📄 Raw request body (decoded):")
        print(decoded_text)

        # Just return success so RChilli stops retrying
        return jsonify({"status": "Payload received in safe mode ✅"}), 200

    except Exception as e:
        print("❌ Safe mode error:", str(e))
        return jsonify({"error": "Unexpected failure", "message": str(e)}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
