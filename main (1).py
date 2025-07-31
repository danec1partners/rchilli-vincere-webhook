
import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

CLIENT_ID = os.environ.get("VINCERE_CLIENT_ID")
CLIENT_SECRET = os.environ.get("VINCERE_CLIENT_SECRET")
TENANT_DOMAIN = os.environ.get("VINCERE_DOMAIN")
AUTH_URL = os.environ.get("VINCERE_AUTH_URL")

def get_access_token():
    payload = {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = requests.post(AUTH_URL, data=payload, headers=headers)
    if response.status_code == 200:
        return response.json().get('access_token')
    else:
        print("Failed to get token:", response.text)
        return None

@app.route('/', methods=['GET'])
def home():
    return "✅ RChilli to Vincere webhook is running!"

@app.route('/', methods=['POST'])
def webhook():
    try:
        content_type = request.headers.get('Content-Type', '')
        print("🔍 Content-Type:", content_type)

        if 'application/json' in content_type:
            data = request.get_json(force=True)
            print("✅ JSON payload received:", data)

        elif 'multipart/form-data' in content_type:
            data = request.form.to_dict()
            print("📎 Form data received:", data)

        else:
            raw = request.data.decode('utf-8')
            print("📄 Raw payload received:", raw)
            data = {}  # fallback

        return jsonify({"status": "Payload received successfully ✅"}), 200

    except Exception as e:
        print("❌ Webhook error:", str(e))
        return jsonify({"error": "Webhook failed", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
