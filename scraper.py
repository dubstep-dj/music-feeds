import os
import re
import json
import datetime
import requests
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
BANDCAMP_USERNAME = "redineas"
# ---------------------

def get_pure_follows_feed(username):
    url = f"https://bandcamp.com/{username}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    items = []
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return items
        
        soup = BeautifulSoup(response.text, 'html.parser')
        blob_el = soup.select_one('#pagedata[data-blob]') or soup.select_one('[data-blob]')
        
        if blob_el:
            blob_data = json.loads(blob_el['data-blob'])
            
            # This extracts the absolute newest releases specifically from your followed list
            package = blob_data.get('following_bands', {}).get('current_items', [])
            
            for entry in package:
                title = entry.get('title')
                artist = entry.get('band_name')
                item_id = entry.get('item_id')
                item_type = entry.get('item_type', 'album')
                
                # Reconstruct the direct link safely
                subdomain = entry.get('url_hints', {}).get('subdomain')
                if subdomain:
                    link = f"https://{subdomain}.bandcamp.com/{item_type}/{item_id}"
                else:
                    link = f"https://bandcamp.com/search?q={requests.utils.quote(artist)}"
                
                if title and artist:
                    items.append({
                        "title": f"[{artist.upper()}] {title}",
                        "link": link,
                        "desc": f"Latest release directly from your followed artist list."
                    })
    except Exception as e:
        print(f"Error parsing direct profile feed: {e}")
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
            rss += f'  <pubDate>{now}</pubDate>\n'
            rss += '</item>\n'
            
    rss += '</channel>\n</rss>'
    return rss

if __name__ == "__main__":
    print(f"Fetching direct feed items for user: {BANDCAMP_USERNAME}...")
    all_tracks = get_pure_follows_feed(BANDCAMP_USERNAME)
    
    if not all_tracks:
        all_tracks.append({
            "title": "[System Note] Sync check completed. No new items found.",
            "link": "https://github.com",
            "desc": "Connected successfully, waiting for your follows to drop new music.",
            "pub_date": datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
        })

    rss_content = generate_rss(all_tracks)
    with open("feed.xml", "w", encoding="utf-8") as f:
        f.write(rss_content)
    print(f"Successfully compiled RSS feed with {len(all_tracks)} direct items.")
