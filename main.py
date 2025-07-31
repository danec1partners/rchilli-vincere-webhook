@app.route('/', methods=['POST'])
def webhook():
    try:
        content_type = request.headers.get('Content-Type', '')
        print("🔍 Content-Type:", content_type)

        if 'application/json' in content_type:
            data = request.get_json(force=True)
            print("✅ JSON payload received:", data)

        elif 'multipart/form-data' in content_type:
            data = request.form.to_dict()
            print("📎 Form data received:", data)

        else:
            raw = request.data.decode('utf-8')
            print("📄 Raw payload received:", raw)
            data = {}  # fallback if needed

        return jsonify({"status": "Payload received successfully ✅"}), 200

    except Exception as e:
        print("❌ Webhook error:", str(e))
        return jsonify({"error": "Webhook failed", "message": str(e)}), 500
