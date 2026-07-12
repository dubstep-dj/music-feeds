import json
import sys
import requests
from bs4 import BeautifulSoup

BANDCAMP_USERNAME = "redineas"

def clear_diagnostic():
    url = f"https://bandcamp.com/{username}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    print(f"--- STARTING DIAGNOSTIC FOR: {url} ---")
    response = requests.get(url, headers=headers, timeout=15)
    print(f"HTTP Status Received: {response.status_code}")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    blob_el = soup.select_one('#pagedata[data-blob]') or soup.select_one('[data-blob]')
    
    if not blob_el:
        print("CRITICAL FAILURE: Bandcamp did not return a data-blob structural block to this server.")
        sys.exit("Execution halted: Empty data-blob wrapper.")
        
    print("SUCCESS: Data-blob structural block located.")
    blob_data = json.loads(blob_el['data-blob'])
    
    # Print out the exact top-level keys available on your specific profile page
    print("\n=== AVAILABLE DATA KEYS IN YOUR PROFILE ===")
    print(json.dumps(list(blob_data.keys()), indent=2))
    
    # Look deeper into target areas and print their exact interior structures
    print("\n=== DETAILED KEY STRUCTURES ===")
    for key in ['following_bands', 'fan_data', 'feed_data', 'tracklist']:
        if key in blob_data:
            if isinstance(blob_data[key], dict):
                print(f"'{key}' interior keys: {list(blob_data[key].keys())}")
            else:
                print(f"'{key}' data type: {type(blob_data[key])}")
                
    print("\n--- DIAGNOSTIC COMPLETE ---")
    # Intentionally crash the script so GitHub Actions marks it red and forces the log window open
    sys.exit("Forced crash to read console output.")

if __name__ == "__main__":
    username = BANDCAMP_USERNAME
    clear_diagnostic()
