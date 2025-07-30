@app.route('/', methods=['POST'])
def webhook():
    try:
        raw_data = request.data.decode('utf-8')
        print("🔹 Raw request body:\n", raw_data)

        data = request.get_json(force=True, silent=True)

        if not data:
            return jsonify({"error": "Invalid or empty JSON received"}), 400

        print("✅ Parsed data:", data)

        first_name = data.get('FirstName') or 'NoName'
        last_name = data.get('LastName') or 'NoSurname'
        email = data.get('Email') or 'unknown@example.com'
        mobile = data.get('Mobile') or 'N/A'
        resume_url = data.get('ResumeFileName') or ''

        candidate_data = {
            "firstName": first_name,
            "lastName": last_name,
            "email": email,
            "mobile": mobile,
            "cvFileUrl": resume_url
        }

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
