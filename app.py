import os
import random
import re
import smtplib
from email.message import EmailMessage
import requests
from flask import Flask, jsonify, render_template, request
from randomizer import random_language_search, random_filename_search, get_supported_languages, QuotaExceededError, YOUTUBE_API_KEY, YOUTUBE_SEARCH_URL

app = Flask(__name__, template_folder='.')


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/debug")
def debug():
    key = YOUTUBE_API_KEY
    r = requests.get(YOUTUBE_SEARCH_URL, params={
        "part": "snippet", "q": "hello", "type": "video",
        "maxResults": 1, "key": key
    }, timeout=10)
    return jsonify({"key_present": bool(key), "yt_status": r.status_code, "yt_response": r.json()})


@app.route("/api/languages")
def languages():
    return jsonify(get_supported_languages())


API_KEY_PATTERN = re.compile(r"^AIza[0-9A-Za-z_-]{35}$")


@app.route("/api/submit-key", methods=["POST"])
def submit_key():
    key = ((request.get_json(silent=True) or {}).get("key") or "").strip()
    if not API_KEY_PATTERN.match(key):
        return jsonify({"error": "That doesn't look like a YouTube API key."}), 400

    # videos.list costs 1 quota unit, so this is a cheap check that the key works
    check = requests.get("https://www.googleapis.com/youtube/v3/videos", params={
        "part": "id", "id": "dQw4w9WgXcQ", "key": key
    }, timeout=10)
    if check.status_code != 200:
        return jsonify({"error": "YouTube rejected that key. Make sure the YouTube Data API v3 is enabled for it."}), 400

    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    notify_email = os.getenv("NOTIFY_EMAIL") or smtp_user
    if not (smtp_user and smtp_password and notify_email):
        return jsonify({"error": "Key submission isn't set up yet."}), 500

    msg = EmailMessage()
    msg["Subject"] = "RYG: new YouTube API key submitted"
    msg["From"] = smtp_user
    msg["To"] = notify_email
    msg.set_content(f"Someone submitted a working YouTube API key:\n\n{key}\n")
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as smtp:
            smtp.login(smtp_user, smtp_password)
            smtp.send_message(msg)
    except Exception:
        return jsonify({"error": "Couldn't send right now. Try again later."}), 500

    return jsonify({"ok": True})


@app.route("/api/random")
def get_random_video():
    if not YOUTUBE_API_KEY:
        return jsonify({"error": "API key not set"}), 500

    try:
        lang = request.args.get("lang") or None
        use_language = bool(lang) or random.random() < 0.75
        method = "language" if use_language else "filename"
        print(f"[method] {method} | lang={lang or 'any'}")

        url = random_language_search(lang_code=lang) if use_language else random_filename_search()
        if not url:
            return jsonify({"error": f"No valid link returned from '{method}' method"}), 500

        video_id = url.split("v=")[1]
        return jsonify({"video_id": video_id, "method": method})
    except QuotaExceededError:
        return jsonify({"error": "quota_exceeded"}), 429
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
