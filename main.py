from flask import Flask, request, jsonify
import base64
import os
import requests

app = Flask(__name__)

VINCERE_DOMAIN = os.getenv("VINCERE_DOMAIN")
VINCERE_CLIENT_ID = os.getenv("VINCERE_CLIENT_ID")
VINCERE_CLIENT_SECRET = os.getenv("VINCERE_CLIENT_SECRET")
VINCERE_AUTH_URL = os.getenv("VINCERE_AUTH_URL")

def get_access_token():
    auth_payload = {
        "grant_type": "client_credentials",
        "client_id": VINCERE_CLIENT_ID,
        "client_secret": VINCERE_CLIENT_SECRET
    }
    response = requests.post(VINCERE_AUTH_URL, data=auth_payload)
    response.raise_for_status()
    return response.json().get("access_token")

def find_existing_candidate(email, phone, access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"https://{VINCERE_DOMAIN}/vincere/api/candidate"
    params = {"$filter": f"email eq '{email}'"} if email else {"$filter": f"phone eq '{phone}'"}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()
    return data[0] if data else None

def upload_cv(candidate_id, file_path, access_token):
    url = f"https://{VINCERE_DOMAIN}/vincere/api/document/candidate/{candidate_id}"
    headers = {"Authorization": f"Bearer {access_token}"}

    with open(file_path, 'rb') as f:
        files = {"file": (os.path.basename(file_path), f, "application/pdf")}
        response = requests.post(url, headers=headers, files=files)
        print(f"📎 CV upload status: {response.status_code} {response.text}")

def create_or_update_candidate(candidate_data, file_path):
    try:
        access_token = get_access_token()
        print("🔐 Access token retrieved.")

        existing = find_existing_candidate(candidate_data["email"], candidate_data["phone"], access_token)
        print(f"🧠 Existing candidate: {existing}")

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        if existing:
            candidate_id = existing["id"]
            url = f"https://{VINCERE_DOMAIN}/vincere/api/candidate/{candidate_id}"
            print(f"🔄 Updating candidate ID: {candidate_id}")
            update_response = requests.put(url, headers=headers, json=candidate_data)
            print(f"🔄 Update response: {update_response.status_code} - {update_response.text}")
        else:
            url = f"https://{VINCERE_DOMAIN}/vincere/api/candidate"
            print("➕ Creating new candidate")
            response = requests.post(url, headers=headers, json=candidate_data)
            print(f"➕ Creation response: {response.status_code} - {response.text}")
            candidate_id = response.json().get("id")

        upload_cv(candidate_id, file_path, access_token)

    except Exception as e:
        print("❌ Error in create_or_update_candidate:", str(e))

@app.route("/", methods=["POST"])
def webhook():
    print("📥 POST received")
    content_type = request.headers.get("Content-Type", "")
    print("📄 Content-Type:", content_type)

    try:
        raw_data = request.get_json(force=True)
        print("🧾 JSON payload received:", raw_data)

        resume_info = raw_data.get("ResumeInbox", {})
        if not resume_info or "Base64Data" not in resume_info:
            print("❌ No ResumeInbox or Base64Data found in payload")
            return jsonify({"error": "No Base64Data found"}), 400

        base64_data = resume_info["Base64Data"]
        email = resume_info.get("EmailId", "unknown@example.com")
        file_bytes = base64.b64decode(base64_data)
        file_path = f"/tmp/{email.replace('@', '_at_')}_resume.pdf"

        with open(file_path, "wb") as f:
            f.write(file_bytes)
        print(f"📄 Resume file saved as: {file_path}")

        candidate_data = {
            "firstName": resume_info.get("FirstName", ""),
            "lastName": resume_info.get("LastName", ""),
            "email": email,
            "phone": resume_info.get("Phone", ""),
            "source": "RChilli Webhook",
            "status": "New Lead"
        }

        create_or_update_candidate(candidate_data, file_path)
        return jsonify({"status": "Candidate processed and CV uploaded"}), 200

    except Exception as e:
        print("❌ Error processing webhook:", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
