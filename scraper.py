import os
import re
import json
import datetime
import requests
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
BANDCAMP_USERNAME = "redineas"
# ---------------------

def run_diagnostic(username):
    url = f"https://bandcamp.com/{username}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    diagnostic_log = {
        "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "status_code": 0,
        "html_length": 0,
        "blob_found": False,
        "blob_keys": [],
        "extracted_items_count": 0,
        "raw_blob_preview": {}
    }
    
    items = []
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        diagnostic_log["status_code"] = response.status_code
        diagnostic_log["html_length"] = len(response.text)
        
        if response.status_code != 200:
            return items, diagnostic_log
            
        soup = BeautifulSoup(response.text, 'html.parser')
        blob_el = soup.select_one('#pagedata[data-blob]') or soup.select_one('[data-blob]')
        
        if blob_el:
            diagnostic_log["blob_found"] = True
            blob_data = json.loads(blob_el['data-blob'])
            diagnostic_log["blob_keys"] = list(blob_data.keys())
            
            # Save a clean preview of the top-level keys to inspect structure
            for key in list(blob_data.keys()):
                if isinstance(blob_data[key], dict):
                    diagnostic_log["raw_blob_preview"][key] = list(blob_data[key].keys())
                else:
                    diagnostic_log["raw_blob_preview"][key] = str(type(blob_data[key]))

            # Attempt extraction from common locations
            package = blob_data.get('following_bands', {}).get('current_items', []) or \
                      blob_data.get('feed_data', {}).get('items', []) or \
                      blob_data.get('tracklist', [])
                      
            diagnostic_log["extracted_items_count"] = len(package)
            
            for entry in package[:10]: # Log up to 10 items to analyze format
                title = entry.get('title') or entry.get('item_title')
                artist = entry.get('band_name') or entry.get('artist_name')
                
                if title and artist:
                    items.append({
                        "title": f"[{artist.upper()}] {title}",
                        "link": entry.get('link') or f"https://bandcamp.com/search?q={requests.utils.quote(artist)}",
                        "desc": "Direct item from diagnostic trace loop."
                    })
                    
    except Exception as e:
        diagnostic_log["error_exception"] = str(e)
        
    return items, diagnostic_log

def generate_rss(items):
    now = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
    rss = '<?xml version="1.0" encoding="UTF-8" ?>\n'
    rss += '<rss version="2.0">\n<channel>\n'
    rss += '<title>My Automated Bandcamp Digging Feed</title>\n'
    rss += f'<link>https://bandcamp.com/{BANDCAMP_USERNAME}</link>\n'
    rss += '<description>Live updates directly synced from your followed artists</description>\n'
    rss += f'<pubDate>{now}</pubDate>\n'
    
    for item in items:
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
    all_tracks, diagnostic_data = run_diagnostic(BANDCAMP_USERNAME)
    
    # CRITICAL: Save the diagnostic log as a clean JSON file
    with open("debug_log.json", "w", encoding="utf-8") as debug_file:
        json.dump(diagnostic_data, debug_file, indent=2)
        
    if not all_tracks:
        all_tracks.append({
            "title": "[Diagnostic Mode] Check debug_log.json for details.",
            "link": "https://github.com",
            "desc": f"Run completed at {diagnostic_data['timestamp']}. Please review the diagnostic file.",
        })

    rss_content = generate_rss(all_tracks)
    with open("feed.xml", "w", encoding="utf-8") as f:
        f.write(rss_content)
    print("Diagnostics saved successfully.")
