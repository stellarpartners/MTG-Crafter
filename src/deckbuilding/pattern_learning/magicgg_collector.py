"""
Decklist Collector for Pattern Learning Feature

This module implements the data collection and curation process.
It:
  - Loads raw decklists from a specified directory.
  - Applies cleaning and standardization routines (e.g., normalizing card names).
  - Saves the cleaned decklists to an output directory.
  - Optionally tracks versioning/metadata (here simplified).

Future enhancements can include mapping alternate card names to canonical names,
advanced cleaning logic, and integration with external APIs/updated datasets.
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import csv
import logging
from typing import List, Set, Dict  # Add this import for type hints
import time
import hashlib
import traceback

# Constants - ensure these match deck_scraper.py
CACHE_DIR = Path("cache/pattern_learning")
SOURCE_DIR = CACHE_DIR / "magicgg"  # New source-specific directory
URLS_FILE = SOURCE_DIR / "decklist_urls.csv"

class DecklistCollector:
    def __init__(self):
        """Initialize the collector with source-specific paths"""
        # Set up source-specific directories
        self.source_dir = SOURCE_DIR
        self.decks_dir = self.source_dir / "decks"
        self.raw_dir = self.source_dir / "raw"
        self.cleaned_dir = self.source_dir / "cleaned"
        
        # Create all necessary directories
        for directory in [self.source_dir, self.decks_dir, self.raw_dir, self.cleaned_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        self.crawled_urls = self.load_existing_urls()
        self.hash_file = self.source_dir / "url_hashes.json"
        self.url_hashes = self.load_url_hashes()
    
    def load_raw_decklists(self) -> list:
        """
        Load raw decklist files from the raw decklists directory.
        Assumes each decklist is a JSON file.
        Returns a list of deck dictionaries.
        """
        decklists = []
        # Look for all JSON files in the raw directory (non-recursive)
        for file_path in self.raw_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    deck = json.load(f)
                    deck['source_file'] = file_path.name  # track source filename
                    decklists.append(deck)
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
        return decklists

    def normalize_card_name(self, card_name: str) -> str:
        """
        Normalize card names to a canonical format.
        This is a stub function; for now, it trims and title cases the name.
        Future improvements can apply a mapping dictionary.
        """
        return card_name.strip().title()

    def clean_decklist(self, deck: dict) -> dict:
        """
        Clean and standardize a single decklist.
        Expects deck to have at least a 'deck_name' (or similar identifying field) 
        and a 'cards' list where each card item contains a 'card_name' and 'quantity'.
        """
        cleaned_deck = {}
        # Standardize deck identifier
        cleaned_deck["deck_name"] = deck.get("deck_name", "Unnamed Deck")
        cleaned_deck["source_file"] = deck.get("source_file", "unknown")
        cleaned_deck["ingested_at"] = datetime.now().isoformat()
        
        # Process cards: expect each card to be represented as a dict
        cleaned_cards = []
        # Allow for multiple formats: list of dicts or a dict mapping card names to quantities.
        if isinstance(deck.get("cards"), list):
            # Example: [{'card_name': 'Black Lotus', 'quantity': 1}, ...]
            for card in deck["cards"]:
                name = card.get("card_name", "").strip()
                if name:
                    cleaned_name = self.normalize_card_name(name)
                    cleaned_cards.append({
                        "card_name": cleaned_name,
                        "quantity": card.get("quantity", 1)
                    })
        elif isinstance(deck.get("cards"), dict):
            # Example: {"Black Lotus": 1, "Ancestral Recall": 1}
            for name, quantity in deck["cards"].items():
                cleaned_name = self.normalize_card_name(name)
                cleaned_cards.append({
                    "card_name": cleaned_name,
                    "quantity": quantity
                })
        else:
            print("Deck {} has unrecognized card data structure.".format(cleaned_deck["deck_name"]))
        
        cleaned_deck["cards"] = cleaned_cards
        return cleaned_deck

    def save_cleaned_decklist(self, deck: dict):
        """
        Save a cleaned decklist to the cleaned decklists directory.
        Creates one file per deck, naming the file with the deck's name and a timestamp.
        """
        safe_deck_name = re.sub(r'\W+', '_', deck["deck_name"]).strip("_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_deck_name}_{timestamp}.json"
        file_path = self.cleaned_dir / filename
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(deck, f, indent=2)
            print(f"Cleaned decklist saved: {filename}")
        except Exception as e:
            print(f"Error saving decklist {filename}: {e}")

    def load_existing_urls(self) -> Set[str]:
        """Load existing decklist URLs from the CSV file"""
        urls = set()
        if URLS_FILE.exists():
            try:
                with open(URLS_FILE, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    header = next(reader, None)  # skip header
                    for row in reader:
                        if row:
                            urls.add(row[0])
            except Exception as e:
                print(f"Error loading existing URLs: {e}")
        return urls

    def load_url_hashes(self) -> Dict[str, str]:
        """Load the URL hash registry"""
        if self.hash_file.exists():
            with open(self.hash_file, 'r') as f:
                return json.load(f)
        return {}
    
    def calculate_url_hash(self, url: str) -> str:
        """Calculate a hash for a URL, normalizing it first"""
        # Remove any trailing slashes, query params, etc
        normalized_url = url.split('?')[0].rstrip('/')
        return hashlib.md5(normalized_url.encode()).hexdigest()

    def fetch_decklist_urls(self, base_url: str) -> list:
        """
        Fetch decklist URLs from the specified Magic.gg page and follow pagination.
        Returns a list of new URLs found on the page.
        """
        new_urls = []
        page_number = 1
        
        while True:
            try:
                # Construct the URL for the current page
                url = f"{base_url}?page={page_number}"
                print(f"\nFetching page {page_number}: {url}")
                
                response = requests.get(url)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')

                # Debug: Print all links found on the page
                print("\nAll links found on page:")
                all_links = soup.find_all('a', href=True)
                print(f"Found {len(all_links)} total links")
                
                decklist_count = 0
                # Find all relevant links
                for link in all_links:
                    href = link['href']
                    # Print all links that contain 'decklists'
                    if 'decklists' in href.lower():
                        print(f"Found decklist link: {href}")
                        decklist_count += 1
                    
                    # Convert relative URLs to absolute URLs
                    if href.startswith('/decklists/'):
                        absolute_url = "https://magic.gg" + href
                        if absolute_url not in self.crawled_urls and 'traditional-standard-ranked-decklists' in absolute_url.lower():
                            new_urls.append(absolute_url)
                            print(f"Added new URL: {absolute_url}")
                
                print(f"\nFound {decklist_count} decklist links on this page")
                print(f"Added {len(new_urls)} new unique URLs so far")

                # Check for pagination elements
                print("\nLooking for pagination elements:")
                pagination = soup.find(['nav', 'div'], class_=lambda x: x and 'pagination' in x.lower())
                if pagination:
                    print("Found pagination section:")
                    print(pagination.prettify())
                
                # Try multiple ways to find the next button
                next_button = None
                next_selectors = [
                    ('a', {'string': lambda s: s and 'next' in s.lower()}),
                    ('a', {'class_': 'next'}),
                    ('button', {'string': lambda s: s and 'next' in s.lower()}),
                    ('a', {'rel': 'next'}),
                    ('link', {'rel': 'next'})
                ]
                
                for tag, attrs in next_selectors:
                    next_button = soup.find(tag, **attrs)
                    if next_button:
                        print(f"Found next button using {tag} with {attrs}:")
                        print(next_button.prettify())
                        break
                
                if not next_button:
                    print(f"No next button found on page {page_number}, stopping pagination")
                    break

                page_number += 1
                time.sleep(1)  # Be nice to the server

            except Exception as e:
                print(f"Error fetching decklist URLs from page {page_number}: {e}")
                print("Full traceback:", traceback.format_exc())
                break

        print(f"\nFinished collecting URLs. Found {len(new_urls)} new unique URLs total")
        return new_urls

    def save_decklist_urls(self, urls: List[str]) -> None:
        """Save new URLs, avoiding duplicates based on hash"""
        try:
            SOURCE_DIR.mkdir(parents=True, exist_ok=True)
            
            new_urls = []
            for url in urls:
                url_hash = self.calculate_url_hash(url)
                if url_hash not in self.url_hashes:
                    new_urls.append(url)
                    self.url_hashes[url_hash] = url
            
            if not new_urls:
                print("No new unique URLs to save")
                return
                
            # Save new URLs to CSV
            write_header = not URLS_FILE.exists()
            with open(URLS_FILE, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if write_header:
                    writer.writerow(['url'])
                for url in new_urls:
                    writer.writerow([url])
            
            # Update hash registry
            self.save_url_hashes()
            
            print(f"Saved {len(new_urls)} new unique URLs to {URLS_FILE}")
            
        except Exception as e:
            print(f"Error saving URLs: {e}")

    def save_url_hashes(self):
        """Save the URL hash registry"""
        with open(self.hash_file, 'w') as f:
            json.dump(self.url_hashes, f, indent=2)

    def update_decklists(self):
        """
        Full processing pipeline:
        - Fetches and saves decklist URLs from Magic.gg
        - Processes any raw decklists found
        """
        print("Starting decklist collection and curation...")
        
        # Fetch and save decklist URLs
        print("Fetching decklist URLs from Magic.gg...")
        decklist_urls = self.fetch_decklist_urls("https://magic.gg/decklists")
        if decklist_urls:
            print(f"Found {len(decklist_urls)} new URLs")
            self.save_decklist_urls(decklist_urls)
        else:
            print("No new URLs found")

        # Process raw decklists if any exist
        raw_decklists = self.load_raw_decklists()
        if not raw_decklists:
            print(f"No raw decklists found in {self.raw_dir}")
        else:
            print(f"Processing {len(raw_decklists)} raw decklists...")
            for deck in raw_decklists:
                cleaned_deck = self.clean_decklist(deck)
                self.save_cleaned_decklist(cleaned_deck)
        
        print("Decklist collection and curation completed.")

if __name__ == "__main__":
    collector = DecklistCollector()
    collector.update_decklists() 