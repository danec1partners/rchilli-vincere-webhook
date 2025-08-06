import base64
import zipfile
import io
import json
from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

@app.route('/', methods=['POST'])
def webhook():
    print("📥 POST received")

    content_type = request.headers.get('Content-Type', '')
    print("📄 Content-Type:", content_type)

    try:
        raw_data = request.get_json(force=True)
        print("🧾 JSON payload received:", raw_data)

        rchilli_info = raw_data.get("RChilliEmailInfo", {})

        if not rchilli_info or "Base64Data" not in rchilli_info:
            print("❌ No RChilliEmailInfo found in payload")
            return jsonify({"error": "No resume JSON found in zip"}), 400

        # Decode and unzip resume
        zip_data = base64.b64decode(rchilli_info["Base64Data"])
        with zipfile.ZipFile(io.BytesIO(zip_data), 'r') as zip_ref:
            print("📂 Files in ZIP:", zip_ref.namelist())
            
            found_json = False

            for file_name in zip_ref.namelist():
                print(f"🔍 Checking file: {file_name}")
                if file_name.endswith('.json'):
                    found_json = True
                    with zip_ref.open(file_name) as json_file:
                        resume_data = json.load(json_file)
                        print("📄 Resume JSON extracted:", resume_data)

                        # Extract key details
                        first_name = resume_data.get("FirstName", "")
                        last_name = resume_data.get("LastName", "")
                        email = resume_data.get("Email", "")
                        phone = resume_data.get("Mobile", "")
                        address = resume_data.get("Address", "")
                        
                        print(f"👤 Candidate: {first_name} {last_name} | {email}")

                        send_to_vincere({
                            "firstName": first_name,
                            "lastName": last_name,
                            "email": email,
                            "phone": phone,
                            "address": address,
                            "source": "RChilli Webhook",
                            "status": "New Lead"
                        })

                        return jsonify({"status": "Resume parsed and sent"}), 200

            if not found_json:
                print("❌ No .json file found in ZIP")
                return jsonify({"error": "No resume JSON found in zip"}), 400

    except Exception as e:
        print("❌ Error processing webhook:", e)
        return jsonify({"error": str(e)}), 500


def send_to_vincere(payload):
    print("🚀 Sending to Vincere...")
    print("📦 Payload to Vincere:", payload)

    url = f"https://{os.getenv('VINCERE_DOMAIN')}/vincere/api/candidate"
    
    client_id = os.getenv('VINCERE_CLIENT_ID')
    client_secret = os.getenv('VINCERE_CLIENT_SECRET')
    auth_url = os.getenv('VINCERE_AUTH_URL')

    auth_payload = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }

    try:
        token_response = requests.post(auth_url, data=auth_payload)
        token_data = token_response.json()
        access_token = token_data.get("access_token", "")

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        response = requests.post(url, headers=headers, json=payload)
        print("📨 Vincere response:", response.status_code, response.text)

    except Exception as e:
        print("❌ Failed to send to Vincere:", e)
