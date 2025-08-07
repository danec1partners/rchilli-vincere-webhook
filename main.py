from flask import Flask, request, jsonify
import base64
import os
import json

app = Flask(__name__)

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

        # Decode and save CV file
        base64_data = resume_info["Base64Data"]
        email = resume_info.get("EmailId", "unknown")
        file_bytes = base64.b64decode(base64_data)
        file_path = f"/tmp/{email.replace('@', '_at_')}_resume.pdf"

        with open(file_path, "wb") as f:
            f.write(file_bytes)

        print(f"📄 Resume file saved as: {file_path}")

        return jsonify({"status": "File processed"}), 200

    except Exception as e:
        print("❌ Error processing webhook:", str(e))
        return jsonify({"error": str(e)}), 500
