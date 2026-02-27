import requests
from bs4 import BeautifulSoup
import json
import time

# Configuration
URL = "https://atthegateway.com/calendar/"
OUTPUT_FILE = "gateway_events.json"

# Enhanced Headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}

def clean_text(text):
    if text:
        return ' '.join(text.split())
    return ""

def scrape_calendar():
    print(f"Fetching calendar from {URL}...")
    time.sleep(1)

    try:
        response = requests.get(URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching page: {e}")
        return [{
            "title": "Visit The Gateway Website",
            "date": "Check Website",
            "description": "Unable to fetch latest events automatically. Scan QR code for details.",
            "image": ""
        }]

    soup = BeautifulSoup(response.content, "html.parser")
    events_data = []

    # Strategy: Select the PARENT container (.tribe-events-calendar-list__event-row)
    # This contains both the image wrapper AND the details wrapper.
    event_cards = soup.select(".tribe-events-calendar-list__event-row")
    
    # Fallback to older class if modern one isn't found
    if not event_cards:
        event_cards = soup.select(".type-tribe_events")

    print(f"Found {len(event_cards)} event entries.")

    count = 0
    for card in event_cards:
        if count >= 9: 
            break

        # 1. EXTRACT TITLE
        title_tag = card.select_one(".tribe-events-calendar-list__event-title, .tribe-events-list-event-title")
        if not title_tag: 
            continue
        title = clean_text(title_tag.get_text())

        # 2. EXTRACT DATE
        time_tag = card.select_one("time")
        if time_tag:
            date_text = clean_text(time_tag.get_text())
        else:
            meta_tag = card.select_one(".tribe-event-schedule-details")
            date_text = clean_text(meta_tag.get_text()) if meta_tag else "See details"

        # 3. EXTRACT DESCRIPTION
        desc_tag = card.select_one(".tribe-events-calendar-list__event-description, .tribe-events-list-event-description")
        description = clean_text(desc_tag.get_text()) if desc_tag else ""
        if len(description) > 100:
            description = description[:97] + "..."

        # 4. EXTRACT IMAGE (New)
        image_src = ""
        img_tag = card.select_one(".tribe-events-calendar-list__event-featured-image-wrapper img, .tribe-events-event-image img")
        
        if img_tag:
            # Try to get the specific 'src' or sometimes lazy loaded 'data-src'
            # We prefer the raw source to ensure we can scale it down ourselves in CSS without pixelation
            raw_src = img_tag.get("src") or img_tag.get("data-src") or ""
            
            # Clean the URL to ensure we get the full size (remove query params like ?resize=...)
            if raw_src:
                # Use the provided URL as-is. It often includes resizing parameters (e.g. ?resize=...)
                # which are better for performance than fetching the full-resolution original.
                image_src = raw_src

        events_data.append({
            "title": title,
            "date": date_text,
            "description": description,
            "image": image_src
        })
        count += 1

    if not events_data:
        events_data.append({
            "title": "Visit The Gateway Website",
            "date": "Daily",
            "description": "Scan the QR code to see the full calendar of events.",
            "image": "" 
        })

    return events_data

def save_json(data):
    with open(OUTPUT_FILE, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Saved {len(data)} events to {OUTPUT_FILE}")

if __name__ == "__main__":
    events = scrape_calendar()
    save_json(events)