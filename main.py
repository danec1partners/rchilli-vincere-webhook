import os
import json
from flask import Flask, request, jsonify
import requests


# Flask application to receive parsed resume data from RChilli and forward it to Vincere.
#
# This version assumes that the parsed resume data is provided directly in the
# "ResumeParserData" field of the JSON payload. It does **not** attempt to
# decode the Base64-encoded resume file itself (which contains the original
# Word/PDF document). Instead, it extracts candidate details from the
# structured JSON returned by RChilli.
#
# Environment variables expected:
# - VINCERE_CLIENT_ID: OAuth client ID from Vincere
# - VINCERE_CLIENT_SECRET: OAuth client secret from Vincere
# - VINCERE_DOMAIN: Base domain/tenant for Vincere (e.g. ec1.vincere.io)
# - VINCERE_AUTH_URL: URL for obtaining OAuth tokens (e.g. https://ec1.vincere.io/oauth/token)
# - SESSION_SECRET: Any random string used by Flask (not critical for this API)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "supersecret")

# Load Vincere credentials from environment
CLIENT_ID = os.environ.get("VINCERE_CLIENT_ID")
CLIENT_SECRET = os.environ.get("VINCERE_CLIENT_SECRET")
TENANT_ID = os.environ.get("VINCERE_DOMAIN")  # e.g. ec1.vincere.io
AUTH_URL = os.environ.get("VINCERE_AUTH_URL")


def get_access_token():
    """
    Obtain a bearer token from Vincere using client credentials flow.

    Returns:
        str or None: The access token, or None on failure.
    """
    if not all([CLIENT_ID, CLIENT_SECRET, AUTH_URL]):
        print("⚠️  Missing Vincere OAuth credentials in environment")
        return None

    try:
        payload = {
            'grant_type': 'client_credentials',
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        response = requests.post(AUTH_URL, data=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data.get('access_token')
    except Exception as exc:
        print(f"❌ Error obtaining Vincere token: {exc}")
        return None


@app.route('/', methods=['GET'])
def home():
    """Health endpoint for quick checks."""
    return "✅ RChilli to Vincere webhook running"


@app.route('/', methods=['POST'])
def webhook():
    """
    Receive parsed resume data from RChilli and send to Vincere.

    The expected payload from RChilli should contain a "ResumeParserData" field
    with the candidate's details in JSON format. This function extracts
    name, email and phone number from that structure and uses Vincere's API
    to create a candidate. If required fields are missing or any exceptions
    occur, appropriate HTTP error codes are returned.
    """
    try:
        print("📥 POST received")
        # Attempt to parse the JSON body from the request. Using force=True
        # allows Flask to attempt to parse even if content-type header is
        # incorrect.
        payload = request.get_json(force=True, silent=True)
        if not payload:
            print("⚠️  Invalid or empty JSON in request body")
            return jsonify({"error": "Invalid or empty JSON"}), 400

        # Debug: log the first 1000 characters of the payload to Render logs.
        try:
            print("📦 Full incoming payload (truncated):")
            payload_str = json.dumps(payload, indent=2)
            print(payload_str[:1000])
        except Exception as exc:
            print(f"⚠️  Could not stringify payload: {exc}")

        # Extract the parsed resume data. It should be under the "ResumeParserData" key.
        resume_data = payload.get('ResumeParserData', {})
        if not resume_data:
            print("⚠️  No ResumeParserData found in payload")
            return jsonify({"error": "Missing ResumeParserData"}), 400

        # Extract candidate fields. RChilli uses nested structures for name
        # and lists for contact details (email/phone). Safely handle missing fields.
        name_info = resume_data.get('Name', {})
        first_name = name_info.get('FirstName') or name_info.get('First', '')
        last_name = name_info.get('LastName') or name_info.get('Last', '')

        email_list = resume_data.get('Email') or []
        email = ''
        if email_list and isinstance(email_list[0], dict):
            email = email_list[0].get('EmailAddress', '') or email_list[0].get('Email', '')

        phone_list = resume_data.get('PhoneNumber') or []
        phone = ''
        if phone_list and isinstance(phone_list[0], dict):
            phone = phone_list[0].get('Number', '') or phone_list[0].get('Phone', '')

        # Build the payload for Vincere. At minimum, provide name and email.
        candidate_payload = {
            "firstName": first_name or "Unknown",
            "lastName": last_name or "Unknown",
            "email": email or "unknown@example.com",
            "mobile": phone or "N/A"
        }

        print("📤 Sending to Vincere:", candidate_payload)

        # Obtain access token for Vincere
        token = get_access_token()
        if not token:
            return jsonify({"error": "Authentication to Vincere failed"}), 500

        # Prepare headers and endpoint for candidate creation
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'tenantId': TENANT_ID or ''
        }
        endpoint = f'https://{TENANT_ID}/v2/candidates' if TENANT_ID else ''
        if not endpoint:
            print("⚠️  Missing TENANT_ID environment variable")
            return jsonify({"error": "Missing tenant configuration"}), 500

        # Send data to Vincere
        try:
            resp = requests.post(endpoint, json=candidate_payload, headers=headers)
            print(f"🔁 Vincere response status: {resp.status_code}")
            try:
                print("🔁 Vincere response body:", resp.text)
            except Exception:
                pass
            if resp.status_code == 201:
                return jsonify({"status": "Candidate created successfully"}), 201
            else:
                return jsonify({
                    "error": "Vincere API returned error", 
                    "status_code": resp.status_code,
                    "detail": resp.text
                }), resp.status_code
        except Exception as exc:
            print(f"❌ Exception when sending to Vincere: {exc}")
            return jsonify({"error": "Exception in Vincere API call", "message": str(exc)}), 500

    except Exception as exc:
        # Catch any other exceptions and log them. Return generic 500.
        print(f"❌ Exception in webhook handler: {exc}")
        return jsonify({"error": "Internal server error", "message": str(exc)}), 500


if __name__ == '__main__':
    # Use the port assigned by environment or default to 10000
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)