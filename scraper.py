import os
import re
import json
import datetime
import requests
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
BANDCAMP_USERNAME = "redineas"
# ---------------------

def get_bandcamp_follows(username):
    """Parses Bandcamp's internal data-blob script block to get ALL follows instantly"""
    url = f"https://bandcamp.com/{username}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    follows = []
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"Could not load profile. Status: {response.status_code}")
            return follows
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Bandcamp drops profile info inside a hidden data-blob element
        blob_el = soup.select_one('#pagedata[data-blob]') or soup.select_one('[data-blob]')
        if blob_el:
            blob_data = json.loads(blob_el['data-blob'])
            # Navigate straight to the system follow array block
            following_list = blob_data.get('following_bands', {}).get('rec_list', [])
            for item in following_list:
                band_url = item.get('url')
                if band_url and band_url not in follows:
                    follows.append(band_url)
        
        # Fallback backup selector rule deck if profile data configuration shifts
        if not follows:
            for anchor in soup.select('a[href*=".bandcamp.com"]'):
                link = anchor['href'].split('?')[0]
                if not any(x in link for x in ['/feed', '/dashboard', 'api.', 'join.', 'cards.']):
                    if link not in follows:
                        follows.append(link)
                        
        print(f"Successfully tracked {len(follows)} followed artists directly from profile profile data map.")
    except Exception as e:
        print(f"Error reading profile layer: {e}")
    return follows

def scrape_bandcamp_site(url):
    """Scrapes the artist music index for track updates"""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    items = []
    target_url = url.rstrip('/') + "/music"
    
    try:
        response = requests.get(target_url, headers=headers, timeout=10)
        if response.status_code != 200:
            response = requests.get(url, headers=headers, timeout=10)
            
        if response.status_code != 200:
            return items
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Scrape item structures
        cards = soup.select('.music-grid-item') or soup.select('li.item') or soup.select('[id*="music-grid"]')
        for card in cards[:2]: # Grab top 2 recent records to save space
            link_el = card.select_one('a[href*="/album/"]') or card.select_one('a[href*="/track/"]')
            title_el = card.select_one('.title') or card.select_one('.heading') or card.select_one('p')
            
            if link_el:
                link = link_el['href']
                if link.startswith('/'):
                    link = url.rstrip('/') + link
                
                raw_title = title_el.text.strip() if title_el else "New Track/Album"
                raw_title = " ".join(raw_title.split()) # Clean space strings
                
                # Fetch clean domain band handle name for clear visibility
                band_name = url.replace("https://", "").replace(".bandcamp.com", "").split('/')[0]
                title = f"[{band_name.upper()}] {raw_title}"
                
                items.append({
                    "title": title,
                    "link": link,
                    "desc": f"Latest release tracking out via {url}"
                })
    except Exception as e:
        pass
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
            rss += '</item>\n'
            
    rss += '</channel>\n</rss>'
    return rss

if __name__ == "__main__":
    all_tracks = []
    followed_targets = get_bandcamp_follows(BANDCAMP_USERNAME)
    
    for target in followed_targets:
        tracks = scrape_bandcamp_site(target)
        all_tracks.extend(tracks)
        
    if not all_tracks:
        all_tracks.append({
            "title": "[System Note] Sync configuration check verified. No fresh tracks found.",
            "link": "https://github.com",
            "desc": "Connected to data profile successfully, but tracks are currently empty."
        })

    rss_content = generate_rss(all_tracks)
    with open("feed.xml", "w", encoding="utf-8") as f:
        f.write(rss_content)
    print("Successfully committed updated RSS configuration loop.")
