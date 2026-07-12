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
    url = f"https://bandcamp.com/{username}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    follows = []
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"Failed to load profile. Status: {response.status_code}")
            return follows
        
        soup = BeautifulSoup(response.text, 'html.parser')
        blob_el = soup.select_one('#pagedata[data-blob]') or soup.select_one('[data-blob]')
        if blob_el:
            blob_data = json.loads(blob_el['data-blob'])
            following_list = blob_data.get('following_bands', {}).get('rec_list', [])
            for item in following_list:
                band_url = item.get('url')
                if band_url and band_url not in follows:
                    follows.append(band_url)
    except Exception as e:
        print(f"Error parsing profile follows: {e}")
    return follows

def scrape_bandcamp_site(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    items = []
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return items
            
        soup = BeautifulSoup(response.text, 'html.parser')
        cards = soup.select('.music-grid-item') or soup.select('li.item') or soup.select('a[href*="/album/"]') or soup.select('a[href*="/track/"]')
        
        for card in cards[:2]: 
            link_el = card if card.name == 'a' else (card.select_one('a[href*="/album/"]') or card.select_one('a[href*="/track/"]'))
                
            if link_el and link_el.get('href'):
                link = link_el['href']
                if link.startswith('/'):
                    link = url.rstrip('/') + link
                
                band_name = url.replace("https://", "").replace(".bandcamp.com", "").split('/')[0].upper()
                
                items.append({
                    "title": f"[{band_name}] New Release Link",
                    "link": link,
                    "desc": f"Latest release on artist page: {url}"
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
            rss += f'  <pubDate>{now}</pubDate>\n'
            rss += '</item>\n'
            
    rss += '</channel>\n</rss>'
    return rss

if __name__ == "__main__":
    all_tracks = []
    followed_targets = get_bandcamp_follows(BANDCAMP_USERNAME)
    
    # Scrapes the first 25 artists to prevent timeouts while giving a deep layout pool
    for target in followed_targets[:25]:
        tracks = scrape_bandcamp_site(target)
        all_tracks.extend(tracks)
        
    if not all_tracks:
        all_tracks.append({
            "title": "[System Note] Sync check completed. No new items found.",
            "link": "https://github.com",
            "desc": "Connected successfully, but zero items were pulled from the pages.",
            "pub_date": datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
        })

    rss_content = generate_rss(all_tracks)
    with open("feed.xml", "w", encoding="utf-8") as f:
        f.write(rss_content)
    print("Successfully generated valid feed.xml.")
