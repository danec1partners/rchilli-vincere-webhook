import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

VINCERE_API_KEY = os.environ.get("VINCERE_API_KEY")
VINCERE_BASE_URL = os.environ.get("VINCERE_BASE_URL")  # e.g. https://api.vincere.io

def send_to_vincere(candidate_data):
    try:
        print("📤 Sending to Vincere")

        headers = {
            "x-api-key": VINCERE_API_KEY,
            "Content-Type": "application/json"
        }

        payload = {
            "firstName": candidate_data.get("Name", {}).get("FirstName", ""),
            "lastName": candidate_data.get("Name", {}).get("LastName", ""),
            "email": candidate_data.get("Email", [{}])[0].get("EmailAddress", ""),
            "phone": candidate_data.get("PhoneNumber", [{}])[0].get("FormattedNumber", ""),
            "currentLocation": candidate_data.get("Address", [{}])[0].get("City", ""),
            "source": "RChilli Webhook",
            "summary": candidate_data.get("DetailResume", ""),
        }

        url = f"{VINCERE_BASE_URL}/candidates"
        response = requests.post(url, json=payload, headers=headers)

        print("🔁 Vincere response")
        print(response.status_code)
        print(response.text)

        return response.status_code, response.text

    except Exception as e:
        print("❌ Error sending to Vincere:", str(e))
        return 500, str(e)


@app.route('/', methods=['GET'])
def home():
    return "✅ RChilli to Vincere webhook is live"

@app.route('/', methods=['POST'])
def webhook():
    try:
        print("📥 POST received")

        content_type = request.headers.get('Content-Type', '')
        if 'application/json' in content_type:
            raw_data = request.get_json(force=True)
        else:
            raw_data = request.data.decode('utf-8')
            print("⚠️ Unexpected content type:", content_type)
            return jsonify({"error": "Unsupported content type"}), 400

        print("🔍 Parsing RChilliEmailInfo")
        parsed_data = raw_data.get("RChilliEmailInfo", {})

        if not parsed_data:
            print("❌ No RChilliEmailInfo found in payload")
            return jsonify({"error": "Missing RChilliEmailInfo"}), 400

        print("👤 Candidate Name:", parsed_data.get("Name", {}).get("FullName", "N/A"))
        print("📧 Email:", parsed_data.get("Email", [{}])[0].get("EmailAddress", "N/A"))

        status, message = send_to_vincere(parsed_data)

        return jsonify({"status": "Processed", "vincere_status": status, "message": message}), 200

    except Exception as e:
        print("❌ Webhook error:", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
