from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")


@app.route('/', methods=['GET'])
def home():
    return "✅ RChilli to Vincere webhook is alive!"


@app.route('/', methods=['POST'])
def webhook():
    try:
        print("📥 POST received")
        print("📄 Content-Type:", request.headers.get('Content-Type', ''))

        # Parse JSON data
        raw_data = request.get_json(force=True)
        print("🧾 JSON payload received:", raw_data)

        # Extract RChilliEmailInfo
        print("🔍 Parsing RChilliEmailInfo")
        parsed_data = raw_data.get("RChilliEmailInfo", {})

        # Basic candidate info
        resume = parsed_data.get("ResumeParserData", {})
        name = resume.get("Name", {})
        email_list = resume.get("Email", [])
        phone_list = resume.get("PhoneNumber", [])
        address_list = resume.get("Address", [])

        candidate = {
            "firstName": name.get("FirstName", ""),
            "lastName": name.get("LastName", ""),
            "email": email_list[0]["EmailAddress"] if email_list else "",
            "phone": phone_list[0]["FormattedNumber"] if phone_list else "",
            "address": address_list[0]["FormattedAddress"] if address_list else ""
        }

        print("👤 Candidate Name:", name.get("FormattedName", "N/A"))
        print("📧 Email:", candidate["email"])

        send_to_vincere(candidate)

        return jsonify({"status": "Processed ✅"}), 200

    except Exception as e:
        print("❌ Error in webhook:", str(e))
        return jsonify({"error": "Webhook failed", "message": str(e)}), 400


def send_to_vincere(candidate):
    url = "https://api.vincere.io/v2/candidate"

    headers = {
        "Authorization": f"Bearer {os.getenv('VINCERE_ACCESS_TOKEN')}",
        "Content-Type": "application/json"
    }

    payload = {
        "firstName": candidate.get("firstName", ""),
        "lastName": candidate.get("lastName", ""),
        "email": candidate.get("email", ""),
        "phone": candidate.get("phone", ""),
        "address": candidate.get("address", ""),
        "source": "RChilli Webhook",
        "status": "New Lead"
    }

    print("🚀 Sending to Vincere...")
    print("📦 Payload to Vincere:", payload)

    try:
        response = requests.post(url, headers=headers, json=payload)
        print("📨 Vincere response:", response.status_code, response.text)
    except Exception as e:
        print("❌ Error sending to Vincere:", str(e))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
