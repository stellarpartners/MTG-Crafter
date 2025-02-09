"""
Deck Scraper for Pattern Learning Feature

This module crawls Magic.gg deck URLs and extracts deck details including card lists.
Works in conjunction with decklist_collector.py to process collected URLs.
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import csv
import time
from urllib.parse import urljoin
import hashlib
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Constants - Match paths with decklist_collector.py
BASE_URL = "https://magic.gg"
CACHE_DIR = Path("cache/pattern_learning")
SOURCE_DIR = CACHE_DIR / "magicgg"  # New source-specific directory
DECKS_DIR = SOURCE_DIR / "decks"
URLS_FILE = SOURCE_DIR / "decklist_urls.csv"

def load_urls_to_process() -> List[str]:
    """
    Load URLs from the CSV file that haven't been processed yet.
    """
    if not URLS_FILE.exists():
        print(f"URLs file not found at {URLS_FILE}")
        print("Please run decklist_collector.py first to gather URLs")
        return []
        
    urls = []
    try:
        SOURCE_DIR.mkdir(parents=True, exist_ok=True)  # Ensure source directory exists
        with open(URLS_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                print("CSV file is empty or malformed")
                return []
            for row in reader:
                url = row.get('url', '').strip()
                if url and url.startswith(BASE_URL):
                    urls.append(url)
        print(f"Loaded {len(urls)} URLs from {URLS_FILE}")
        return urls
    except Exception as e:
        print(f"Error loading URLs: {e}")
        return []

def parse_card_line(line: str) -> Optional[Tuple[str, str]]:
    """
    Parse a line containing card information in the format "N CardName"
    
    Args:
        line: String containing quantity and card name
        
    Returns:
        Tuple of (quantity, card_name) if successful, None otherwise
    """
    try:
        # Match patterns like "4 Card Name" or "2 Card Name"
        match = re.match(r'(\d+)\s+(.+)', line.strip())
        if match:
            quantity, card_name = match.groups()
            return quantity, card_name.strip()
    except Exception as e:
        print(f"Error parsing card line '{line}': {e}")
    return None

def extract_decklists(text: str) -> List[Dict[str, List[Dict[str, str]]]]:
    """
    Extract multiple decklists from the page content.
    """
    decklists = []
    current_cards = []
    in_decklist = False
    
    print("\nAnalyzing content for decklists...")
    
    # Split text into lines and process each line
    lines = text.split('\n')
    print(f"Found {len(lines)} lines of content")
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Skip empty lines unless we're in a decklist
        if not line:
            if in_decklist and current_cards:
                decklists.append({"cards": current_cards})
                print(f"Completed decklist with {len(current_cards)} cards")
                current_cards = []
                in_decklist = False
            continue
        
        # Check for decklist markers
        deck_markers = ["Deck", "Main Deck", "Mainboard", "Main Board", "Cards"]
        if any(marker in line for marker in deck_markers):
            print(f"Found deck marker: {line}")
            in_decklist = True
            continue
            
        if in_decklist:
            # Try to parse the line as a card entry
            card_info = parse_card_line(line)
            if card_info:
                quantity, card_name = card_info
                current_cards.append({
                    "quantity": quantity,
                    "card_name": card_name
                })
                print(f"Added card: {quantity}x {card_name}")
    
    # Add the last decklist if there are remaining cards
    if current_cards:
        decklists.append({"cards": current_cards})
        print(f"Added final decklist with {len(current_cards)} cards")
    
    return decklists

def scrape_deck(url: str) -> dict:
    """
    Crawl a given deck URL and extract deck details.
    """
    try:
        print(f"\nScraping deck from: {url}")
        
        # First get the page to extract any needed metadata
        response = requests.get(url)
        response.raise_for_status()
        
        # The deck data is loaded via API, construct the API URL
        # Example: /decklists/traditional-standard-ranked-decklists-january-27-2025
        # becomes: /api/decklists/traditional-standard-ranked-decklists-january-27-2025
        api_url = url.replace("/decklists/", "/api/decklists/")
        print(f"Fetching deck data from API: {api_url}")
        
        # Add headers to look like a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Referer': url
        }
        
        # Fetch the deck data from the API
        api_response = requests.get(api_url, headers=headers)
        api_response.raise_for_status()
        
        # Parse the JSON response
        deck_data = api_response.json()
        print(f"API Response status: {api_response.status_code}")
        print("API Response preview:")
        print(json.dumps(deck_data, indent=2)[:500])
        
        # If we don't get JSON data, try alternative API URL patterns
        if not deck_data or api_response.status_code != 200:
            alt_api_url = f"{url}/data"
            print(f"Trying alternative API URL: {alt_api_url}")
            api_response = requests.get(alt_api_url, headers=headers)
            api_response.raise_for_status()
            deck_data = api_response.json()
        
        return {
            "url": url,
            "deck_title": deck_data.get("title", "Unknown Deck"),
            "decklists": deck_data.get("decklists", []),
            "scraped_at": datetime.now().isoformat(),
            "raw_data": deck_data  # Store the complete response for future processing
        }

    except Exception as e:
        print(f"Error scraping deck from {url}: {e}")
        print("Full traceback:", traceback.format_exc())
        return {}

def calculate_deck_hash(deck_data: dict) -> str:
    """
    Calculate a unique hash for a deck based on its contents.
    The hash is based on the sorted list of cards and their quantities.
    """
    if not deck_data.get("decklists"):
        return ""
        
    # Get all cards from all decklists in sorted order
    all_cards = []
    for decklist in deck_data["decklists"]:
        cards = decklist.get("cards", [])
        all_cards.extend([f"{card['quantity']}x{card['card_name']}" for card in cards])
    
    # Sort to ensure same deck with different card order gets same hash
    all_cards.sort()
    
    # Create a string representation and hash it
    deck_string = "|".join(all_cards)
    return hashlib.md5(deck_string.encode()).hexdigest()

def save_deck_data(deck_data: dict) -> None:
    """
    Save the scraped deck data as a JSON file.
    
    Args:
        deck_data: Dictionary containing deck details
    """
    try:
        DECKS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Calculate deck hash
        deck_hash = calculate_deck_hash(deck_data)
        if not deck_hash:
            print("Warning: Empty deck data, skipping...")
            return
            
        # Check if we already have this deck
        hash_file = SOURCE_DIR / "deck_hashes.json"
        existing_hashes = {}
        if hash_file.exists():
            with open(hash_file, 'r') as f:
                existing_hashes = json.load(f)
        
        if deck_hash in existing_hashes:
            print(f"Duplicate deck found, skipping (matches {existing_hashes[deck_hash]})")
            return
            
        # Save the deck
        safe_title = re.sub(r'\W+', '_', deck_data.get("deck_title", "deck")).strip("_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_title}_{timestamp}.json"
        file_path = DECKS_DIR / filename

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(deck_data, f, indent=2)
            
        # Update hash registry
        existing_hashes[deck_hash] = filename
        with open(hash_file, 'w') as f:
            json.dump(existing_hashes, f, indent=2)
            
        print(f"Deck data saved to: {file_path}")
        
    except Exception as e:
        print(f"Error saving deck data: {e}")

def process_all_urls():
    """
    Main function to process all URLs from the CSV file.
    Uses Selenium to handle JavaScript-rendered content.
    """
    print("Starting deck scraping process...")
    
    # Ensure directories exist
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    DECKS_DIR.mkdir(parents=True, exist_ok=True)
    
    if not URLS_FILE.exists():
        print(f"\nError: URLs file not found at {URLS_FILE}")
        print("Please run decklist_collector.py first to gather URLs")
        return
    
    # Load URLs to process
    urls = load_urls_to_process()
    if not urls:
        print("No valid URLs found to process")
        print("Please ensure decklist_collector.py has successfully gathered URLs")
        return
        
    print(f"Found {len(urls)} URLs to process")
    
    # Set up Chrome options once
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    # Process each URL with a single browser instance
    with webdriver.Chrome(options=options) as driver:
        for i, url in enumerate(urls, 1):
            print(f"\nProcessing URL {i}/{len(urls)}: {url}")
            
            # Scrape the deck using Selenium
            deck_data = scrape_deck_with_selenium(url, driver)
            
            if deck_data and deck_data.get("decklists"):
                print(f"Successfully scraped {len(deck_data['decklists'])} decklists")
                
                # Show preview of first decklist
                if deck_data["decklists"]:
                    first_deck = deck_data["decklists"][0]
                    print("\nFirst decklist preview:")
                    for card in first_deck["cards"][:5]:
                        print(f"  {card['quantity']}x {card['card_name']}")
                    if len(first_deck["cards"]) > 5:
                        print("  ...")
                
                # Save the data
                save_deck_data(deck_data)
            else:
                print("Failed to scrape deck data from this URL")
            
            # Be nice to the server
            time.sleep(2)
    
    print("\nDeck scraping process completed!")

def scrape_deck_with_selenium(url: str, driver: webdriver.Chrome) -> dict:
    """
    Scrape deck using Selenium to handle JavaScript rendering.
    """
    try:
        print(f"\nScraping deck from: {url}")
        driver.get(url)
        
        # Wait for any dynamic content to load
        print("Waiting for page to load...")
        time.sleep(5)  # Initial wait for page load
        
        # Print page title and URL to verify we're on the right page
        print(f"Current page title: {driver.title}")
        print(f"Current URL: {driver.current_url}")
        
        # Get the page source and look for key elements
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        # Debug: Print all div classes to help identify deck containers
        print("\nFound div elements with classes:")
        for div in soup.find_all('div', class_=True):
            print(f"- {div.get('class')}")
        
        # Extract deck data from the fully rendered page
        deck_data = {
            "url": url,
            "deck_title": "Traditional Standard Ranked Decklists",
            "decklists": [],
            "scraped_at": datetime.now().isoformat()
        }
        
        # Find the deck title
        title_elem = soup.find("h1")
        if title_elem:
            deck_data["deck_title"] = title_elem.get_text(strip=True)
            print(f"Found title: {deck_data['deck_title']}")
        
        # Look for any elements containing card information
        print("\nLooking for card elements...")
        
        # Try multiple approaches to find card information
        card_containers = []
        
        # Approach 1: Look for elements with card-related text
        for elem in soup.find_all(['div', 'span', 'p']):
            text = elem.get_text(strip=True)
            if re.match(r'^\d+\s+[A-Za-z]', text):  # Matches patterns like "4 Lightning Bolt"
                print(f"Found potential card: {text}")
                card_containers.append(elem)
        
        # Approach 2: Look for structured card elements
        card_elements = soup.find_all(class_=lambda x: x and any(term in str(x).lower() 
            for term in ['card', 'deck-card', 'deckcard', 'deck-list-card']))
        
        if card_elements:
            print(f"\nFound {len(card_elements)} structured card elements")
            cards = []
            for card_elem in card_elements:
                # Print the full element for debugging
                print(f"\nCard element HTML:")
                print(card_elem.prettify())
                
                # Try to extract quantity and name
                text = card_elem.get_text(strip=True)
                match = re.match(r'^(\d+)\s+(.+)$', text)
                if match:
                    quantity, name = match.groups()
                    cards.append({
                        "quantity": quantity,
                        "card_name": name
                    })
                    print(f"Extracted: {quantity}x {name}")
            
            if cards:
                deck_data["decklists"].append({"cards": cards})
                print(f"\nAdded decklist with {len(cards)} cards")
        
        # Approach 3: Look for text-based deck lists
        if not deck_data["decklists"]:
            print("\nTrying text-based approach...")
            text_content = soup.get_text()
            deck_lines = [line.strip() for line in text_content.split('\n') 
                         if re.match(r'^\d+\s+[A-Za-z]', line.strip())]
            
            if deck_lines:
                print(f"Found {len(deck_lines)} potential card lines")
                cards = []
                for line in deck_lines:
                    match = re.match(r'^(\d+)\s+(.+)$', line)
                    if match:
                        quantity, name = match.groups()
                        cards.append({
                            "quantity": quantity,
                            "card_name": name
                        })
                        print(f"Extracted: {quantity}x {name}")
                
                if cards:
                    deck_data["decklists"].append({"cards": cards})
                    print(f"\nAdded decklist with {len(cards)} cards")
        
        return deck_data
            
    except Exception as e:
        print(f"Error scraping deck from {url}: {e}")
        print("Full traceback:", traceback.format_exc())
        return {}

if __name__ == "__main__":
    process_all_urls() 