import sys
import requests
from bs4 import BeautifulSoup

BANDCAMP_USERNAME = "redineas"

def inspect_raw_html():
    url = f"https://bandcamp.com/{BANDCAMP_USERNAME}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    print(f"--- FETCHING DATA FOR: {url} ---")
    response = requests.get(url, headers=headers, timeout=15)
    print(f"Server Response Status: {response.status_code}")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 1. Print out the basic text structure of the page header
    if soup.title:
        print(f"Page Title Found: {soup.title.text.strip()}")
    
    # 2. Look for any visible links or text elements to see what kind of profile view we got
    links = [a.get('href') for a in soup.find_all('a') if a.get('href')]
    print(f"Total HTML Links Found on Page: {len(links)}")
    if links:
        print("Sample of first 5 links:")
        for l in links[:5]:
            print(f" - {l}")
            
    # 3. Dump the first 1000 characters of the raw page layout text directly to the screen
    print("\n=== RAW PAGE SOURCE CODE STARTS HERE ===")
    print(response.text[:1500])
    print("=== RAW PAGE SOURCE CODE ENDS HERE ===\n")
    
    # Crash the script on purpose so the terminal output screen stays open for us
    sys.exit("Forced check: Look at the printed logs above.")

if __name__ == "__main__":
    inspect_raw_html()
