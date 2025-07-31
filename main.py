
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
            raw_data = request.get_json(force=True)
            print("✅ JSON payload received:", raw_data)
        elif 'multipart/form-data' in content_type:
            raw_data = request.form.to_dict()
            print("📎 Form data received:", raw_data)
        else:
            raw_data = request.data.decode('utf-8')
            print("📄 Raw payload received:", raw_data)
            return jsonify({"error": "Unsupported content type"}), 400

        rchilli_data = raw_data.get('RChilliEmailInfo', {})
        print("📦 Parsed RChilliEmailInfo:", rchilli_data)

        first_name = rchilli_data.get('FirstName', 'Unknown')
        last_name = rchilli_data.get('LastName', 'Unknown')
        email_list = rchilli_data.get('EmailAddress', [])
        phone_list = rchilli_data.get('PhoneNumber', [])

        email = email_list[0].get('EmailAddress') if email_list else 'unknown@example.com'
        phone = phone_list[0].get('FormattedNumber') if phone_list else 'N/A'
        resume_url = rchilli_data.get('ResumeFileName', '')

        candidate_data = {
            "firstName": first_name,
            "lastName": last_name,
            "email": email,
            "mobile": phone,
            "cvFileUrl": resume_url
        }

        print("📤 Candidate to Vincere:", candidate_data)

        access_token = get_access_token()
        if not access_token:
            return jsonify({"error": "Failed to authenticate with Vincere"}), 500

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'tenantId': TENANT_DOMAIN
        }

        vincere_url = f'https://{TENANT_DOMAIN}/v2/candidates'
        response = requests.post(vincere_url, json=candidate_data, headers=headers)

        print("🔁 Response from Vincere:", response.text)

        if response.status_code == 201:
            return jsonify({"status": "Candidate sent to Vincere ✅"}), 201
        else:
            return jsonify({"error": "Failed to create candidate in Vincere", "details": response.text}), 400

    except Exception as e:
        print("❌ Webhook error:", str(e))
        return jsonify({"error": "Webhook failed", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
