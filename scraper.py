import os
import re
import datetime
import requests

# --- CONFIGURATION ---
BANDCAMP_USERNAME = "redineas"
# ---------------------

def get_fan_id(username):
    url = f"https://bandcamp.com/{username}"
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            match = re.search(r'fan_id\s*=\s*(\d+)', response.text)
            if match:
                return match.group(1)
            match_meta = re.search(r'/fan/(\d+)/', response.text)
            if match_meta:
                return match_meta.group(1)
    except Exception as e:
        print(f"Error resolving Fan ID: {e}")
    return None

def fetch_past_seven_days(fan_id):
    """Queries Bandcamp's official timeline API to grab the historical 7-day catalog drop"""
    url = "https://bandcamp.com/api/fancorlection/1/feed"
    
    # Payload formatted exactly how the Bandcamp engine expects it
    payload = {
        "fan_id": int(fan_id),
        "cursor": "*",
        "tab": "following"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/json"
    }
    
    items = []
    seven_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=7)
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"API rejection code: {response.status_code}")
            return items
            
        data = response.json()
        events = data.get('feed', [])
        
        for event in events:
            # Only look at actual track or album releases published by your follows
            if event.get('event_type') in ['release', 'publish']:
                title = event.get('item_title')
                artist = event.get('band_name')
                link = event.get('item_url')
                
                # Parse the release date safely
                publish_date_str = event.get('event_date') # e.g., "10 Jul 2026 14:20:00 GMT"
                if publish_date_str:
                    try:
                        # Clean up formatting for string matching
                        date_clean = publish_date_str.split(', ')[-1] if ', ' in publish_date_str else publish_date_str
                        release_date = datetime.datetime.strptime(date_clean[:11], "%d %b %Y")
                    except:
                        release_date = datetime.datetime.utcnow() # Fallback
                else:
                    release_date = datetime.datetime.utcnow()

                # Strictly filter for updates within the 7-day window
                if release_date >= seven_days_ago and title and link:
                    formatted_date = release_date.strftime("%a, %d %b %Y %H:%M:%S GMT")
                    items.append({
                        "title": f"[{artist.upper()}] {title}",
                        "link": link,
                        "desc": f"Released by {artist} within the last 7 days.",
                        "date": formatted_date
                    })
    except Exception as e:
        print(f"Error pulling catalog timeline: {e}")
    return items

def generate_rss(items):
    now = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
    rss = '<?xml version="1.0" encoding="UTF-8" ?>\n'
    rss += '<rss version="2.0">\n<channel>\n'
    rss += '<title>My Automated Bandcamp Digging Feed</title>\n'
    rss += f'<link>https://bandcamp.com/{BANDCAMP_USERNAME}</link>\n'
    rss += '<description>Live updates directly synced from your followed artists</description>\n'
    rss += f'<pubDate>{now}</pubDate>\n'
    
    seen_links = set()
    for item in items:
        if item['link'] not in seen_links:
            seen_links.add(item['link'])
            clean_title = item['title'].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            rss += '<item>\n'
            rss += f'  <title>{clean_title}</title>\n'
            rss += f'  <link>{item["link"]}</link>\n'
            rss += f'  <guid>{item["link"]}</guid>\n'
            rss += f'  <description>{item["desc"]}</description>\n'
            rss += f'  <pubDate>{item["date"]}</pubDate>\n'
            rss += '</item>\n'
            
    rss += '</channel>\n</rss>'
    return rss

if __name__ == "__main__":
    fan_id = get_fan_id(BANDCAMP_USERNAME)
    all_tracks = []
    
    if fan_id:
        print(f"Token resolved: {fan_id}. Pulling 7-day timeline historical catalog...")
        all_tracks = fetch_past_seven_days(fan_id)
        
    if not all_tracks:
        all_tracks.append({
            "title": "[System Note] Sync check completed. No new releases found in the last 7 days.",
            "link": "https://github.com",
            "desc": "Connected cleanly, but your followed artists haven't dropped music this week.",
            "date": datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
        })

    rss_content = generate_rss(all_tracks)
    with open("feed.xml", "w", encoding="utf-8") as f:
        f.write(rss_content)
    print(f"Successfully compiled RSS feed with {len(all_tracks)} items.")
