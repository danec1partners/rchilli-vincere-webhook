import os
from flask import Flask, request, jsonify
import requests
import json

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

VINCERE_API_KEY = os.environ.get("VINCERE_API_KEY")
VINCERE_TENANT_ID = os.environ.get("VINCERE_TENANT_ID")
VINCERE_DOMAIN = os.environ.get("VINCERE_DOMAIN", "https://api.vincere.io")

@app.route('/', methods=['GET'])
def home():
    return "✅ Webhook is live"

@app.route('/', methods=['POST'])
def webhook():
    try:
        print("📥 POST received")
        raw_json = request.get_json(force=True)
        print("📦 Full incoming payload:")
        print(json.dumps(raw_json, indent=2))

        # Handle safe/test webhook mode
        if "ResumeParserData" not in raw_json:
            print("⚠️ No ResumeParserData found. Possibly test mode.")
            return jsonify({"status": "Payload received in safe mode ✅"}), 200

        resume_data = raw_json["ResumeParserData"]
        name = resume_data.get("Name", {})
        first_name = name.get("FirstName", "")
        last_name = name.get("LastName", "")
        email = resume_data.get("Email", [{}])[0].get("EmailAddress", "")
        phone = resume_data.get("PhoneNumber", [{}])[0].get("FormattedNumber", "")

        if not first_name or not last_name or not email:
            print("❌ Missing critical candidate fields")
            return jsonify({"error": "Missing required fields"}), 400

        payload = {
            "firstName": first_name,
            "lastName": last_name,
            "email": email,
            "phone": phone,
            "source": "RChilli Webhook"
        }

        print("📤 Sending to Vincere:", json.dumps(payload))

        headers = {
            "x-api-key": VINCERE_API_KEY,
            "x-tenant-id": VINCERE_TENANT_ID,
            "Content-Type": "application/json"
        }

        response = requests.post(f"{VINCERE_DOMAIN}/v2/candidates", json=payload, headers=headers)

        print("🔁 Vincere response status:", response.status_code)
        print("🔁 Vincere response body:", response.text)

        return jsonify({"status": "Candidate sent to Vincere ✅", "vincere_response": response.text}), 200

    except Exception as e:
        print("❌ Error in webhook:", str(e))
        return jsonify({"error": "Unexpected error", "message": str(e)}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
