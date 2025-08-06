from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# ENV variables
VINCERE_AUTH_URL = os.getenv("VINCERE_AUTH_URL")
VINCERE_CLIENT_ID = os.getenv("VINCERE_CLIENT_ID")
VINCERE_CLIENT_SECRET = os.getenv("VINCERE_CLIENT_SECRET")
VINCERE_DOMAIN = os.getenv("VINCERE_DOMAIN")

# ------------------ AUTH FUNCTION ------------------ #
def get_access_token():
    try:
        data = {
            "grant_type": "client_credentials",
            "client_id": VINCERE_CLIENT_ID,
            "client_secret": VINCERE_CLIENT_SECRET
        }
        response = requests.post(VINCERE_AUTH_URL, data=data)
        response.raise_for_status()
        token = response.json().get("access_token")
        print("✅ Authenticated with Vincere")
        return token
    except Exception as e:
        print("❌ Failed to authenticate:", e)
        return None

# ------------------ SEND TO VINCERE ------------------ #
def send_to_vincere(parsed_data):
    print("🚀 Sending to Vincere...")

    access_token = get_access_token()
    if not access_token:
        return {"error": "Auth failed"}, 500

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    candidate_payload = {
        "firstName": parsed_data.get("FirstName", ""),
        "lastName": parsed_data.get("LastName", ""),
        "email": parsed_data.get("Email", ""),
        "phone": parsed_data.get("Phone", ""),
        "address": parsed_data.get("Address", ""),
        "source": "RChilli Webhook",
        "status": "New Lead"
    }

    print("📦 Payload to Vincere:", candidate_payload)

    try:
        response = requests.post(
            f"https://{VINCERE_DOMAIN}/v2/candidate",
            json=candidate_payload,
            headers=headers
        )
        print("📨 Vincere response:", response.status_code, response.text)
        return {"message": "Candidate sent to Vincere"}, response.status_code
    except Exception as e:
        print("❌ Failed to send to Vincere:", e)
        return {"error": str(e)}, 500

# ------------------ MAIN ROUTE ------------------ #
@app.route("/", methods=["POST"])
def webhook():
    print("📥 POST received")

    content_type = request.headers.get("Content-Type", "")
    print("📄 Content-Type:", content_type)

    try:
        if "application/json" in content_type:
            raw_data = request.get_json(force=True)
            print("🧾 JSON payload received:", raw_data)
        elif "multipart/form-data" in content_type:
            raw_data = request.form.to_dict()
            print("📎 Form data received:", raw_data)
        else:
            raw_data = request.data.decode("utf-8")
            print("📄 Raw payload received:", raw_data)
            return jsonify({"error": "Unsupported content type"}), 400
    except Exception as e:
        print("❌ Failed to parse request:", e)
        return jsonify({"error": str(e)}), 400

    # ------------------ Extract from RChilli ------------------ #
    print("🔍 Parsing RChilliEmailInfo")
    parsed_data = raw_data.get("ResumeInbox", {}).get("RChilliEmailInfo", {})

    if not parsed_data:
        print("❌ No RChilliEmailInfo found in payload")
        return jsonify({"error": "Invalid RChilli payload"}), 400

    # Extract key fields
    candidate_info = {
        "FirstName": parsed_data.get("Name", {}).get("FirstName", ""),
        "LastName": parsed_data.get("Name", {}).get("LastName", ""),
        "Email": parsed_data.get("Email", [{}])[0].get("EmailAddress", ""),
        "Phone": parsed_data.get("PhoneNumber", [{}])[0].get("FormattedNumber", ""),
        "Address": parsed_data.get("Address", [{}])[0].get("FormattedAddress", "")
    }

    print(f"👤 Candidate Name: {candidate_info['FirstName']} {candidate_info['LastName']}")
    print(f"📧 Email: {candidate_info['Email']}")

    return send_to_vincere(candidate_info)

# ------------------ ROOT CHECK ------------------ #
@app.route("/", methods=["GET"])
def health():
    return "✅ Webhook is live!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
