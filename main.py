import os
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)
app.secret_key = os.getenv("SESSION_SECRET")

USER_KEY = os.getenv("RCHILLI_USER_KEY")
SUBUSER_ID = os.getenv("RCHILLI_SUBUSER_ID")
VERSION = os.getenv("RCHILLI_VERSION", "8.0.0")
VINCERE_TOKEN = os.getenv("VINCERE_ACCESS_TOKEN")

@app.route('/', methods=['POST'])
def webhook():
    print("📥 POST received")
    data = request.get_json(force=True)
    print("🧾 Payload:", {k: v for k, v in data.items() if k != "ResumeInbox"})

    inbox = data.get("ResumeInbox", {})
    base64data = inbox.get("Base64Data", "")
    filename = inbox.get("Filename", "resume")

    if not base64data:
        print("❌ No Base64 data in ResumeInbox")
        return jsonify({"error": "Missing ResumeInbox.Base64Data"}), 400

    print("🔄 Sending binary data to RChilli for parsing...")
    r = requests.post(
        "https://rest.rchilli.com/RChilliParser/Rchilli/parseResumeBinary",
        json={
            "filedata": base64data,
            "filename": filename,
            "userkey": USER_KEY,
            "version": VERSION,
            "subuserid": SUBUSER_ID
        }
    )
    print("🔁 RChilli response:", r.status_code)
    parsed = r.json().get("ResumeParserData", {})

    first = parsed.get("Name", {}).get("FirstName","")
    last = parsed.get("Name", {}).get("LastName","")
    email = parsed.get("Email", [{}])[0].get("EmailAddress","")
    phone = parsed.get("PhoneNumber", [{}])[0].get("FormattedNumber","")

    print(f"👤 Parsed: {first} {last}, {email}, {phone}")

    # Send to Vincere
    resp = requests.post(
        "https://api.vincere.io/v2/candidate",
        headers={"Authorization": f"Bearer {VINCERE_TOKEN}", "Content-Type": "application/json"},
        json={
            "firstName": first,
            "lastName": last,
            "email": email,
            "phone": phone,
            "source": "RChilli Webhook"
        }
    )
    print("✅ Vincere returned:", resp.status_code, resp.text)
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
