import random
from flask import Flask, jsonify, render_template
from randomizer import random_language_search, random_filename_search

app = Flask(__name__, template_folder='.')


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/random")
def get_random_video():
    url = random_language_search() if random.random() < 0.75 else random_filename_search()
    if not url:
        return jsonify({"error": "No video found"}), 500
    video_id = url.split("v=")[1]
    return jsonify({"video_id": video_id})


if __name__ == "__main__":
    app.run(debug=True)
