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
