import os
import re
import datetime
import requests
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
# Paste your target URLs inside this list. Enclose each link in quotes and separate them with commas.
TARGET_URLS = [
    "https://www.beatport.com/label/deep-medi-musik/1146",
    "https://bandcamp.com/tag/dubstep"
]
# ---------------------

def scrape_url(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    items = []
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return items
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Checking for Bandcamp entries
        if "bandcamp.com" in url:
            for card in soup.select('li.item')[:15]:
                title_el = card.select_one('.heading')
                sub_el = card.select_one('.subhead')
                link_el = card.select_one('a')
                if title_el and link_el:
                    title = f"[{sub_el.text.strip() if sub_el else 'Bandcamp'}] {title_el.text.strip()}"
                    link = link_el['href'].split('?')[0]
                    items.append({"title": title, "link": link, "desc": f"New release found via {url}"})
                    
        # Checking for Beatport entries
        elif "beatport.com" in url:
            # Beatport keeps track details in structural anchor tags or spans depending on layout updates
            for track in soup.select('a[href*="/track/"], div[class*="TrackRow"] ' )[:15]:
                link_attr = track.get('href', '')
                if "/track/" in link_attr:
                    link = "https://www.beatport.com" + link_attr.split('?')[0]
                    title_text = track.text.strip()
                    if title_text and len(title_text) > 3:
                        items.append({"title": f"[Beatport] {title_text}", "link": link, "desc": f"New entry on Beatport label page: {url}"})
    except Exception as e:
        print(f"Error scraping {url}: {e}")
    return items

def generate_rss(items):
    now = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
    rss = '<?xml version="1.0" encoding="UTF-8" ?>\n'
    rss += '<rss version="2.0">\n<channel>\n'
    rss += '<title>My Custom Music Digging Feed</title>\n'
    rss += f'<link>https://github.com</link>\n'
    rss += '<description>Automated scraped tracks from Beatport and Bandcamp</description>\n'
    rss += f'<pubDate>{now}</pubDate>\n'
    
    # Remove duplicate links discovered during execution
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
    for target in TARGET_URLS:
        all_tracks.extend(scrape_url(target))
        
    if all_tracks:
        rss_content = generate_rss(all_tracks)
        with open("feed.xml", "w", encoding="utf-8") as f:
            f.write(rss_content)
        print(f"Successfully generated feed.xml with {len(all_tracks)} items.")
    else:
        print("No items found. Generating empty baseline feed.")
