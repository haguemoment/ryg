import os
import random
import requests
from flask import Flask, jsonify, render_template
from randomizer import random_language_search, random_filename_search, YOUTUBE_API_KEY, YOUTUBE_SEARCH_URL

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


@app.route("/api/random")
def get_random_video():
    try:
        url = random_language_search() if random.random() < 0.75 else random_filename_search()
        if not url:
            return jsonify({"error": "No video found"}), 500
        video_id = url.split("v=")[1]
        return jsonify({"video_id": video_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
