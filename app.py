import os
import random
import requests
from flask import Flask, jsonify, render_template, request
from randomizer import random_language_search, random_filename_search, get_supported_languages, YOUTUBE_API_KEY, YOUTUBE_SEARCH_URL

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


@app.route("/api/random")
def get_random_video():
    if not YOUTUBE_API_KEY:
        return jsonify({"error": "API key not set"}), 500

    test = requests.get(YOUTUBE_SEARCH_URL, params={
        "part": "snippet", "q": "test", "type": "video", "maxResults": 1, "key": YOUTUBE_API_KEY
    }, timeout=10)
    if test.status_code != 200:
        err = test.json().get("error", {}).get("message", "unknown")
        return jsonify({"error": f"YouTube API rejected key: {test.status_code} — {err}"}), 500

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
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
