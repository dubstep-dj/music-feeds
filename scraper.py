import os
import re
import datetime
import requests
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
# Replace 'YOUR_BANDCAMP_USERNAME' with your actual username (e.g., "leonardo")
BANDCAMP_USERNAME = "redineas"
# ---------------------

def get_bandcamp_follows(username):
    """Visits your public profile and extracts all the artists/labels you follow"""
    url = f"https://bandcamp.com/{username}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    follows = []
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"Could not load Bandcamp profile for {username}. Status: {response.status_code}")
            return follows
            
        soup = BeautifulSoup(response.text, 'html.parser')
        # Bandcamp stores followed item links inside data attributes or anchors on your profile
        for anchor in soup.select('a[href*=".bandcamp.com"]'):
            link = anchor['href'].split('?')[0]
            # Clean the link to get the base bandcamp URL
            if "bandcamp.com" in link and link not in follows:
                # Exclude generic bandcamp assets
                if not any(x in link for x in ['/feed', '/dashboard', 'api.', 'join.']):
                    follows.append(link)
                    
        print(f"Successfully discovered {len(follows)} followed artists/labels from your profile.")
    except Exception as e:
        print(f"Error fetching Bandcamp follows: {e}")
    return follows

def scrape_bandcamp_site(url):
    """Scrapes the 'music' or home page of a specific bandcamp artist/label for releases"""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    items = []
    # Force looking at their music tab directly if possible
    target_url = url.rstrip('/') + "/music"
    
    try:
        response = requests.get(target_url, headers=headers, timeout=10)
        if response.status_code != 200:
            # Fallback to main URL if they don't have a specific /music subpage
            response = requests.get(url, headers=headers, timeout=10)
            
        if response.status_code != 200:
            return items
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Pull items from grid layouts or recent release blocks
        cards = soup.select('.music-grid-item') or soup.select('li.item') or soup.select('.ip-item')
        for card in cards[:3]: # Grab the 3 most recent items per artist to keep feed compact
            link_el = card.select_one('a[href*="/album/"]') or card.select_one('a[href*="/track/"]')
            title_el = card.select_one('.title') or card.select_one('.heading')
            
            if link_el:
                link = link_el['href']
                if link.startswith('/'):
                    link = url.rstrip('/') + link
                
                # Clean up text layout
                raw_title = title_el.text.strip() if title_el else "New Release"
                title = f"[Bandcamp] {raw_title}"
                
                items.append({
                    "title": title,
                    "link": link,
                    "desc": f"Latest release trackable from {url}"
                })
    except Exception as e:
        pass # Silently skip individual failing sub-sites to keep the engine moving
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
    if BANDCAMP_USERNAME == "YOUR_BANDCAMP_USERNAME":
        print("Error: You forgot to update your Bandcamp username inside the script config!")
        exit(1)
        
    all_tracks = []
    # 1. Automatically fetch the master list of everything you follow
    followed_targets = get_bandcamp_follows(BANDCAMP_USERNAME)
    
    # 2. Iterate through every single profile found and harvest new releases
    for target in followed_targets:
        tracks = scrape_bandcamp_site(target)
        all_tracks.extend(tracks)
        
    if not all_tracks:
        all_tracks.append({
            "title": "[System Note] Sync check completed. No new releases found today.",
            "link": "https://github.com",
            "desc": "The engine connected to your follows successfully, but no new music was published."
        })

    rss_content = generate_rss(all_tracks)
    with open("feed.xml", "w", encoding="utf-8") as f:
        f.write(rss_content)
    print(f"Successfully tracked and saved total bundle map.")
