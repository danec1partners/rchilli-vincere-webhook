
import os
import json
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
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = requests.post(AUTH_URL, data=payload, headers=headers)
    return response.json().get('access_token') if response.status_code == 200 else None

@app.route('/', methods=['GET'])
def home():
    return "✅ Webhook ready"

@app.route('/', methods=['POST'])
def webhook():
    try:
        print("📥 POST received")
        data = request.get_json(force=True)
        parsed = data.get("ResumeParserData", {})
        name = parsed.get("Name", {})
        email_list = parsed.get("Email", [])
        phone_list = parsed.get("PhoneNumber", [])

        candidate = {
            "firstName": name.get("FirstName", "Unknown"),
            "lastName": name.get("LastName", "Unknown"),
            "email": email_list[0]["EmailAddress"] if email_list else "unknown@example.com",
            "mobile": phone_list[0]["Number"] if phone_list else "N/A"
        }

        print("📤 Sending to Vincere:", candidate)
        token = get_access_token()
        if not token:
            return jsonify({"error": "Auth failed"}), 500

        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'tenantId': TENANT_DOMAIN
        }

        url = f'https://{TENANT_DOMAIN}/v2/candidates'
        res = requests.post(url, json=candidate, headers=headers)
        print("🔁 Vincere response:", res.text)
        return jsonify({"status": "sent"}), res.status_code

    except Exception as e:
        print("❌ Error:", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
