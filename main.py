from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

def send_to_vincere(parsed_data):
    try:
        print("🚀 Sending to Vincere...")

        # Set up Vincere credentials and endpoint
        vincere_client_id = os.environ.get("VINCERE_CLIENT_ID")
        vincere_client_secret = os.environ.get("VINCERE_CLIENT_SECRET")
        vincere_api_url = os.environ.get("VINCERE_API_URL", "https://api.vincere.io/v2/candidate")

        if not all([vincere_client_id, vincere_client_secret]):
            raise ValueError("Missing Vincere credentials")

        # Compose headers
        headers = {
            "Content-Type": "application/json",
            "x-api-key": vincere_client_id,
            "x-api-secret": vincere_client_secret
        }

        # Map RChilli fields to Vincere format
        candidate_payload = {
            "firstName": parsed_data.get("Name", {}).get("FirstName", ""),
            "lastName": parsed_data.get("Name", {}).get("LastName", ""),
            "email": parsed_data.get("Email", [{}])[0].get("EmailAddress", ""),
            "phone": parsed_data.get("PhoneNumber", [{}])[0].get("FormattedNumber", ""),
            "address": parsed_data.get("Address", [{}])[0].get("FormattedAddress", ""),
            "source": "RChilli Webhook",
            "status": "New Lead"
        }

        print("📦 Payload to Vincere:", candidate_payload)

        # Send request to Vincere
        response = requests.post(vincere_api_url, headers=headers, json=candidate_payload)
        print("📨 Vincere response:", response.status_code, response.text)

        return response.status_code, response.text

    except Exception as e:
        print("❌ Vincere error:", str(e))
        return 500, str(e)

@app.route('/', methods=['GET'])
def home():
    return "✅ RChilli to Vincere webhook is alive"

@app.route('/', methods=['POST'])
def webhook():
    try:
        print("📥 POST received")

        content_type = request.headers.get('Content-Type', '')
        print("📄 Content-Type:", content_type)

        if 'application/json' in content_type:
            raw_data = request.get_json(force=True)
            print("🧾 JSON payload received:")
            print(raw_data)
        else:
            print("❌ Unsupported content type")
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
