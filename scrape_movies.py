import json
import os
import re
import time
from datetime import datetime
from playwright.sync_api import sync_playwright
from PIL import Image
from io import BytesIO
import requests

# Configuration
IMDB_URL = "https://www.imdb.com/showtimes/cinema/US/ci0011810/US/84101/"
OUTPUT_FILE = "movies.json"
POSTER_DIR = "posters"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

def clean_text(text):
    if text:
        return ' '.join(text.split())
    return ""

def slugify(text):
    text = text.lower()
    return re.sub(r'[^a-z0-9]+', '-', text).strip('-')

def download_poster(img_url, title):
    if not img_url:
        return None
    if not os.path.exists(POSTER_DIR):
        os.makedirs(POSTER_DIR)
    filename = f"{slugify(title)}.jpg"
    filepath = os.path.join(POSTER_DIR, filename)
    if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
        return filename
    try:
        print(f"Downloading and optimizing poster for {title}...")
        r = requests.get(img_url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            img = Image.open(BytesIO(r.content))
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            max_width = 400
            if img.width > max_width:
                w_percent = (max_width / float(img.width))
                h_size = int((float(img.height) * float(w_percent)))
                img = img.resize((max_width, h_size), Image.Resampling.LANCZOS)
            img.save(filepath, "JPEG", quality=85, optimize=True)
            return filename
    except Exception as e:
        print(f"Failed to download poster for {title}: {e}")
    return None

def format_runtime(seconds):
    if not seconds:
        return ""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours}h {minutes}m"

def datetime_from_time_str(time_str):
    try:
        return datetime.strptime(time_str, "%I:%M %p")
    except:
        return datetime.min

def scrape_movies():
    print(f"Fetching showtimes from {IMDB_URL} using Playwright...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Use a more natural User-Agent
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        try:
            page.goto(IMDB_URL, wait_until="load", timeout=60000)
            # Wait for either __NEXT_DATA__ or a common showtime selector to confirm it's not the challenge page
            page.wait_for_selector("script#__NEXT_DATA__", state="attached", timeout=15000)
            content = page.content()
        except Exception as e:
            print(f"Error fetching page with Playwright: {e}")
            browser.close()
            return []
        browser.close()

    movies_data = []
    import re
    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', content)
    if not match:
        print("Error: Could not find __NEXT_DATA__ script tag in Playwright output.")
        return []

    try:
        json_data = json.loads(match.group(1))
        titles_data = json_data.get("props", {}).get("pageProps", {}).get("titleAndShowtimeData", [])
        print(f"Found {len(titles_data)} movies in JSON data.")

        for item in titles_data:
            node = item.get("node", {})
            title_obj = node.get("title", {})
            
            title = title_obj.get("titleText", {}).get("text", "")
            if not title:
                continue

            rating_summary = title_obj.get("ratingsSummary", {})
            rating_val = rating_summary.get("aggregateRating", "")
            rating_score = str(rating_val) if rating_val is not None else "NR"
            
            cert_obj = title_obj.get("certificate")
            cert = cert_obj.get("rating", "NR") if cert_obj else "NR"
            
            runtime_obj = title_obj.get("runtime")
            runtime_secs = runtime_obj.get("seconds") if runtime_obj else None
            runtime = format_runtime(runtime_secs)
            
            genres_obj = title_obj.get("titleGenres")
            genres_list = genres_obj.get("genres", []) if genres_obj else []
            genre_text = ""
            if genres_list:
                genre_item = genres_list[0].get("genre")
                genre_text = genre_item.get("text", "") if genre_item else ""

            poster_obj = title_obj.get("primaryImage")
            poster_url = poster_obj.get("url", "") if poster_obj else ""
            
            showtimes = []
            showtime_con = title_obj.get("cinemaShowtimesByScreeningType", {})
            showtime_groups = showtime_con.get("edges", []) if showtime_con else []
            for group in showtime_groups:
                node_st = group.get("node", {})
                types = node_st.get("showtimesByScreeningType", []) if node_st else []
                for t in types:
                    times = t.get("showtimes", []) if t else []
                    for st in times:
                        start_obj = st.get("screeningStart")
                        start_text = start_obj.get("text", "") if start_obj else ""
                        if start_text:
                            showtimes.append(start_text)
            
            showtimes = sorted(list(set(showtimes)), key=lambda x: datetime_from_time_str(x))

            local_poster = ""
            if poster_url:
                local_poster = download_poster(poster_url, title)

            if title and showtimes:
                movies_data.append({
                    "title": title,
                    "rating": cert, 
                    "score": rating_score,
                    "runtime": runtime,
                    "genre": genre_text,
                    "times": showtimes[:12], 
                    "poster": f"posters/{local_poster}" if local_poster else ""
                })

    except Exception as e:
        print(f"Error parsing JSON data: {e}")
        return []

    if len(movies_data) > 0:
        current_posters = [m["poster"].split('/')[-1] for m in movies_data if m["poster"]]
        if os.path.exists(POSTER_DIR):
            for f in os.listdir(POSTER_DIR):
                if f not in current_posters:
                    try:
                        os.remove(os.path.join(POSTER_DIR, f))
                        print(f"Removed old poster: {f}")
                    except:
                        pass
    return movies_data

def save_json(data):
    with open(OUTPUT_FILE, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Saved {len(data)} movies to {OUTPUT_FILE}")

if __name__ == "__main__":
    movies = scrape_movies()
    if not movies:
        print("Scrape returned 0 movies.")
    else:
        save_json(movies)