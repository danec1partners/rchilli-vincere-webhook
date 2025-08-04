
import zipfile
import base64
import io
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
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = requests.post(AUTH_URL, data=payload, headers=headers)
    if response.status_code == 200:
        return response.json().get('access_token')
    else:
        print("❌ Failed to get token:", response.text)
        return None

@app.route('/', methods=['GET'])
def home():
    return "✅ RChilli to Vincere webhook is alive (Payload Inspector Mode)"

@app.route('/', methods=['POST'])
def webhook():
    try:
        print("📥 Incoming POST request")

        raw_json = request.get_json(force=True)
        print("📦 Full incoming payload:")
        print(json.dumps(raw_json, indent=2))

        email_info = raw_json.get("RChilliEmailInfo")
        if not email_info:
            return jsonify({"error": "Missing RChilliEmailInfo"}), 400

        base64_zip = email_info.get("Base64Data")
        if not base64_zip:
            return jsonify({"error": "No Base64Data field found in RChilliEmailInfo"}), 400

        # Decode and unzip
        zip_bytes = base64.b64decode(base64_zip)
        zip_file = zipfile.ZipFile(io.BytesIO(zip_bytes))
        file_list = zip_file.namelist()

        print("📂 ZIP file contains:")
        for name in file_list:
            print(f" - {name}")

        return jsonify({"status": "ZIP decoded and listed", "files": file_list}), 200

    except Exception as e:
        print("❌ Webhook error:", str(e))
        return jsonify({"error": "Webhook failed", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
