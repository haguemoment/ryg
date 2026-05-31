"""
Approach 1: Truly random YouTube video via batch ID checking.
Generates random 11-char base64url IDs, checks 50 at a time via videos.list API.
Saves all checked IDs to CSV to avoid repeats across runs.
"""

import os
import csv
import random
import string
import requests
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
VIDEOS_API_URL = "https://www.googleapis.com/youtube/v3/videos"
ALPHABET = string.ascii_letters + string.digits + "-_"  # 64 chars, base64url
BATCH_SIZE = 50
TOTAL_CHECKS = 600
VALID_CSV = "valid_ids.csv"
INVALID_CSV = "invalid_ids.csv"


def _load_seen_ids():
    seen = set()
    for fname in (VALID_CSV, INVALID_CSV):
        if os.path.exists(fname):
            with open(fname, newline="") as f:
                for row in csv.reader(f):
                    if row:
                        seen.add(row[0])
    return seen


def _append_ids(fname, ids):
    with open(fname, "a", newline="") as f:
        writer = csv.writer(f)
        for vid_id in ids:
            writer.writerow([vid_id])


def _random_id():
    return "".join(random.choices(ALPHABET, k=11))


def _check_batch(ids):
    """Returns set of valid IDs from the given list."""
    params = {
        "part": "id",
        "id": ",".join(ids),
        "key": YOUTUBE_API_KEY,
    }
    r = requests.get(VIDEOS_API_URL, params=params, timeout=10)
    items = r.json().get("items", [])
    return {item["id"] for item in items}


def run(total=TOTAL_CHECKS):
    seen = _load_seen_ids()
    print(f"Loaded {len(seen)} previously checked IDs.")

    all_valid = []
    checked = 0

    while checked < total:
        # Generate a fresh batch of unseen IDs
        batch = []
        while len(batch) < BATCH_SIZE:
            vid_id = _random_id()
            if vid_id not in seen:
                batch.append(vid_id)
                seen.add(vid_id)

        valid = _check_batch(batch)
        invalid = [i for i in batch if i not in valid]

        _append_ids(VALID_CSV, valid)
        _append_ids(INVALID_CSV, invalid)

        all_valid.extend(valid)
        checked += BATCH_SIZE
        print(f"Checked {checked}/{total} — {len(valid)} valid this batch, {len(all_valid)} total valid so far")

    print(f"\n--- Results ({total} IDs checked) ---")
    if all_valid:
        for vid_id in all_valid:
            print(f"https://www.youtube.com/watch?v={vid_id}")
    else:
        print("No valid video IDs found.")


if __name__ == "__main__":
    run()
