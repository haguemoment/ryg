"""
Random YouTube video generator.
Approaches:
  2. random_language_search() — random words from a weighted language
  3. random_filename_search() — default camera filename patterns
"""

import random
import math
import os
import requests
from dotenv import load_dotenv

load_dotenv()

try:
    from wordfreq import top_n_list, available_languages as wf_langs
    WORDFREQ_AVAILABLE = True
except ImportError:
    WORDFREQ_AVAILABLE = False

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"

# (language name, BCP-47 code, approx speakers in millions)
LANGUAGES = [
    ("Mandarin Chinese", "zh", 1120), ("Spanish", "es", 480), ("English", "en", 379),
    ("Hindi", "hi", 341), ("Arabic", "ar", 315), ("Bengali", "bn", 228),
    ("Portuguese", "pt", 221), ("Russian", "ru", 154), ("Japanese", "ja", 128),
    ("Punjabi", "pa", 119), ("German", "de", 100), ("Javanese", "jv", 84),
    ("Korean", "ko", 82), ("French", "fr", 82), ("Telugu", "te", 74),
    ("Marathi", "mr", 73), ("Turkish", "tr", 71), ("Tamil", "ta", 70),
    ("Vietnamese", "vi", 68), ("Urdu", "ur", 66), ("Italian", "it", 62),
    ("Persian", "fa", 60), ("Malay", "ms", 58), ("Thai", "th", 52),
    ("Burmese", "my", 43), ("Kannada", "kn", 43), ("Hausa", "ha", 43),
    ("Swahili", "sw", 40), ("Odia", "or", 38), ("Uzbek", "uz", 35),
    ("Sindhi", "sd", 33), ("Amharic", "am", 32), ("Fula", "ff", 30),
    ("Romanian", "ro", 28), ("Tagalog", "tl", 28), ("Azerbaijani", "az", 27),
    ("Polish", "pl", 45), ("Ukrainian", "uk", 40), ("Igbo", "ig", 27),
    ("Yoruba", "yo", 45), ("Malayalam", "ml", 37), ("Maithili", "mai", 34),
    ("Sinhala", "si", 17), ("Chittagonian", "ctg", 13), ("Khmer", "km", 16),
    ("Twi", "tw", 22), ("Somali", "so", 22), ("Zulu", "zu", 12),
    ("Cebuano", "ceb", 28), ("Nepali", "ne", 17), ("Shona", "sn", 15),
    ("Indonesian", "id", 43), ("Dutch", "nl", 24), ("Uyghur", "ug", 11),
    ("Kazakh", "kk", 14), ("Serbo-Croatian", "sr", 21), ("Greek", "el", 13),
    ("Hungarian", "hu", 13), ("Czech", "cs", 10), ("Belarusian", "be", 7),
    ("Swedish", "sv", 10), ("Catalan", "ca", 10), ("Finnish", "fi", 5),
    ("Hebrew", "he", 9), ("Norwegian", "no", 5), ("Danish", "da", 6),
    ("Slovak", "sk", 5), ("Bulgarian", "bg", 8), ("Turkmen", "tk", 7),
    ("Kirghiz", "ky", 5), ("Tajik", "tg", 8), ("Lao", "lo", 7),
    ("Lingala", "ln", 24), ("Kinyarwanda", "rw", 12), ("Xhosa", "xh", 8),
    ("Afrikaans", "af", 7), ("Haitian Creole", "ht", 12), ("Balochi", "bal", 9),
    ("Tigrinya", "ti", 9), ("Pashto", "ps", 40), ("Kurdish", "ku", 30),
    ("Dari", "prs", 24), ("Tatar", "tt", 7), ("Georgian", "ka", 4),
    ("Albanian", "sq", 8), ("Armenian", "hy", 7), ("Latvian", "lv", 2),
    ("Lithuanian", "lt", 3), ("Estonian", "et", 1), ("Slovenian", "sl", 2),
    ("Macedonian", "mk", 2), ("Welsh", "cy", 1), ("Icelandic", "is", 0),
    ("Maltese", "mt", 0), ("Luxembourgish", "lb", 0), ("Faroese", "fo", 0),
    ("Basque", "eu", 1), ("Galician", "gl", 3), ("Breton", "br", 0),
    ("Irish", "ga", 2), ("Scottish Gaelic", "gd", 0), ("Frisian", "fy", 0),
    ("Corsican", "co", 0), ("Romansh", "rm", 0), ("Occitan", "oc", 0),
]


def _weighted_choice(items, weight_fn):
    weights = [weight_fn(x) for x in items]
    return random.choices(items, weights=weights, k=1)[0]


_WF_LANGS = set(wf_langs()) if WORDFREQ_AVAILABLE else set()
# Only languages with confirmed wordfreq support; others fall back to Wiktionary at runtime
SUPPORTED_LANGUAGES = [l for l in LANGUAGES if l[1] in _WF_LANGS] if _WF_LANGS else LANGUAGES


def _pick_language():
    # sqrt-compress speaker counts to reduce English/Mandarin dominance
    return _weighted_choice(SUPPORTED_LANGUAGES, lambda l: math.sqrt(max(l[2], 0.1)))


def _get_words_wordfreq(lang_code, n=10000):
    langs = wf_langs() if WORDFREQ_AVAILABLE else []
    if lang_code in langs:
        return top_n_list(lang_code, n)
    return None


def _get_words_wiktionary(lang_code, count=5):
    """Fetch random words from that language's Wiktionary edition."""
    url = f"https://{lang_code}.wiktionary.org/w/api.php"
    params = {
        "action": "query", "list": "random",
        "rnnamespace": 0, "rnlimit": count, "format": "json"
    }
    try:
        r = requests.get(url, params=params, timeout=5)
        pages = r.json()["query"]["random"]
        return [p["title"] for p in pages]
    except Exception:
        return []


def _pick_words(lang_code, count=3):
    words = _get_words_wordfreq(lang_code) if WORDFREQ_AVAILABLE else None
    if words:
        # sqrt-weight by frequency rank (index 0 = most common)
        n = len(words)
        weights = [math.sqrt(n - i) for i in range(n)]
        return random.choices(words, weights=weights, k=count)
    else:
        # fallback: Wiktionary random pages
        pool = _get_words_wiktionary(lang_code, count=20)
        return random.sample(pool, min(count, len(pool))) if pool else []


REGION_CODES = [
    "US", "GB", "CA", "AU", "DE", "FR", "JP", "KR", "BR", "MX", "IN", "NG",
    "ZA", "AR", "CL", "CO", "PL", "UA", "RU", "TR", "SA", "EG", "ID", "PH",
    "TH", "VN", "PK", "BD", "IR", "ES", "IT", "NL", "SE", "NO", "FI", "DK",
    "PT", "RO", "CZ", "HU", "GR", "IL", "KE", "GH", "ET", "TZ", "MA", "DZ",
]


def _pick_order():
    r = random.random()
    if r < 0.60:
        return "date"       # newest = fewest views
    elif r < 0.80:
        return "relevance"  # medium views
    else:
        return "viewCount"  # most viewed


class QuotaExceededError(Exception):
    pass


def _youtube_search(query, region_code=None, relevance_language=None, order=None):
    base_params = {
        "part": "snippet", "q": query, "type": "video",
        "maxResults": 5, "key": YOUTUBE_API_KEY,
        "order": order or "relevance",
    }
    if region_code:
        base_params["regionCode"] = region_code
    if relevance_language:
        base_params["relevanceLanguage"] = relevance_language

    # Always try with duration filter first to exclude Shorts
    for duration in ["medium", None]:
        params = dict(base_params)
        if duration:
            params["videoDuration"] = duration
        r = requests.get(YOUTUBE_SEARCH_URL, params=params, timeout=10)
        data = r.json()
        if r.status_code == 403:
            errors = data.get("error", {}).get("errors", [])
            if any(e.get("reason") == "quotaExceeded" for e in errors):
                raise QuotaExceededError()
        items = data.get("items", [])
        if items:
            video = items[min(4, len(items) - 1)]
            vid_id = video["id"]["videoId"]
            return f"https://www.youtube.com/watch?v={vid_id}"
    return None


# ── Public API ────────────────────────────────────────────────────────────────

def get_supported_languages():
    return [{"name": name, "code": code} for name, code, _ in SUPPORTED_LANGUAGES]


def random_language_search(lang_code=None):
    """Return a YouTube URL found via random words from a random language."""
    pool = SUPPORTED_LANGUAGES
    if lang_code:
        pool = [l for l in SUPPORTED_LANGUAGES if l[1] == lang_code] or SUPPORTED_LANGUAGES

    def _attempt(word_count):
        lang = _weighted_choice(pool, lambda l: math.sqrt(max(l[2], 0.1))) if not lang_code else pool[0]
        lang_name, code, _ = lang
        words = _pick_words(code, word_count)
        if not words:
            return None
        query = " ".join(words)
        order = "relevance" if lang_code else _pick_order()
        print(f"[language] {lang_name} ({code}) → '{query}' order={order}")
        return _youtube_search(query, relevance_language=code if lang_code else None, order=order)

    # Tier 1: 10 tries with 2-3 word phrases
    for _ in range(10):
        result = _attempt(random.randint(2, 3))
        if result:
            return result

    # Tier 2: 5 tries with 1 word
    for _ in range(5):
        result = _attempt(1)
        if result:
            return result

    # Tier 3: 5 tries with 1 word, no duration filter (allow Shorts as last resort)
    pool_lang = pool[0][1] if lang_code else None
    for _ in range(5):
        lang = _weighted_choice(pool, lambda l: math.sqrt(max(l[2], 0.1))) if not lang_code else pool[0]
        lang_name, code, _ = lang
        words = _pick_words(code, 1)
        if not words:
            continue
        query = " ".join(words)
        order = "relevance" if lang_code else _pick_order()
        print(f"[language] {lang_name} ({code}) → '{query}' order={order} [no duration filter]")
        r = requests.get(YOUTUBE_SEARCH_URL, params={
            "part": "snippet", "q": query, "type": "video",
            "maxResults": 5, "key": YOUTUBE_API_KEY, "order": order,
            **({"relevanceLanguage": code} if lang_code else {}),
        }, timeout=10)
        items = r.json().get("items", [])
        if items:
            vid_id = items[min(4, len(items) - 1)]["id"]["videoId"]
            return f"https://www.youtube.com/watch?v={vid_id}"

    return None


def random_filename_search(lang_code=None, retries=5):
    """Return a YouTube URL found via a random default camera filename."""
    prefixes = ["IMG", "MOV", "VID", "DSC", "MVI", "CLIP", "FILE"]
    for _ in range(retries):
        prefix = random.choice(prefixes)
        number = random.randint(1, 9999)
        query = f"{prefix}_{number:04d}"
        region = random.choice(REGION_CODES)
        print(f"[filename] query → '{query}' region={region}")
        result = _youtube_search(query, region_code=region, relevance_language=lang_code)
        if result:
            return result
    return None


if __name__ == "__main__":
    print(random_language_search())
    print(random_filename_search())
