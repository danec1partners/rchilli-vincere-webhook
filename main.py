from flask import Flask, request, jsonify
import os
import json
import requests

app = Flask(__name__)

@app.route('/', methods=['POST'])
def webhook():
    try:
        print("📥 POST received")

        content_type = request.headers.get('Content-Type', '')
        print(f"📄 Content-Type: {content_type}")

        if 'application/json' in content_type:
            raw_data = request.get_json(force=True)
            print(f"🧾 JSON payload received: {json.dumps(raw_data)[:300]}...")  # limit length for logs
        elif 'multipart/form-data' in content_type:
            raw_data = request.form.to_dict()
            print(f"📎 Form data received: {raw_data}")
        else:
            raw_data = request.data.decode('utf-8')
            print(f"📄 Raw payload received: {raw_data}")
            return jsonify({"error": "Unsupported content type"}), 400

        print("🔍 Parsing RChilliEmailInfo")
        parsed_data = raw_data.get("RChilliEmailInfo", {})
        print(f"🧠 Parsed RChilliEmailInfo: {json.dumps(parsed_data)[:300]}...")  # again limit log length

        print("🚀 Sending to Vincere...")
        send_to_vincere(parsed_data)

        return jsonify({"status": "Success ✅"}), 200

    except Exception as e:
        print(f"❌ Webhook error: {str(e)}")
        return jsonify({"error": str(e)}), 500


def send_to_vincere(data):
    print("📦 Payload to Vincere:", {
        "firstName": data.get("Name", {}).get("FirstName", ""),
        "lastName": data.get("Name", {}).get("LastName", ""),
        "email": data.get("Email", [{}])[0].get("EmailAddress", ""),
        "phone": data.get("PhoneNumber", [{}])[0].get("FormattedNumber", ""),
        "address": data.get("Address", [{}])[0].get("FormattedAddress", ""),
        "source": "RChilli Webhook",
        "status": "New Lead"
    })
    # 🔐 This is where the API call to Vincere would go


@app.route('/', methods=['GET'])
def root():
    return "👋 Hello from the RChilli → Vincere Webhook"

