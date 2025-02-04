from pathlib import Path
import json
import requests
from datetime import datetime
import time
from typing import List, Dict, Optional
from tqdm import tqdm

from src.database.card_database import CardDatabase

class ScryfallCollector:
    """Handles data collection from Scryfall API"""
    
    BASE_URL = "https://api.scryfall.com"
    SETS_URL = "https://api.scryfall.com/sets"
    
    # Scryfall recommends no more than 10 requests per second
    REQUEST_DELAY = 0.1  # 100ms between requests
    
    def __init__(self, cache_dir: str = "cache/scryfall", skip_load: bool = False):
        self.cache_dir = Path(cache_dir)
        self.sets_dir = self.cache_dir / "sets"
        
        # Create necessary directories
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.sets_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache files
        self.metadata_file = self.cache_dir / "metadata.json"
        
        if not skip_load:
            self.load_metadata()
    
    def load_metadata(self):
        """Load or initialize metadata tracking"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {
                'sets': {},
                'last_update': None
            }
    
    def save_metadata(self):
        """Save current metadata"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def needs_update(self, set_code: str, set_data: Dict) -> bool:
        """Check if a set needs updating"""
        if set_code not in self.metadata['sets']:
            return True
            
        # Some sets might not have updated_at field
        stored_date = self.metadata['sets'][set_code].get('updated_at')
        new_date = set_data.get('updated_at')
        
        # If either date is missing, assume update is needed
        if not stored_date or not new_date:
            return True
            
        return stored_date != new_date
    
    def _wait_for_rate_limit(self):
        """Ensure we don't exceed rate limits"""
        now = time.time()
        time_since_last = now - self.last_request_time
        if time_since_last < self.REQUEST_DELAY:
            time.sleep(self.REQUEST_DELAY - time_since_last)
        self.last_request_time = time.time()
    
    def fetch_all_cards(self, force_download: bool = False) -> bool:
        """Download cards by set with smart caching"""
        print("\nChecking card data...")
        
        # First get sets catalog
        sets_data = self._fetch_sets_catalog(force_download)
        if not sets_data:
            return False
        
        # Filter and sort sets
        filtered_sets = self._filter_sets(sets_data['data'])
        print(f"\nFound {len(filtered_sets)} relevant sets")
        
        # Compare with existing sets
        new_sets = []
        updated_sets = []
        for set_data in filtered_sets:
            set_code = set_data['code']
            if set_code not in self.metadata['sets']:
                new_sets.append(set_data)
            elif self.needs_update(set_code, set_data):
                updated_sets.append(set_data)
        
        # Show download plan
        if new_sets:
            print(f"\nNew sets to download ({len(new_sets)}):")
            for set_data in new_sets:
                print(f"- {set_data['name']} ({set_data['code']})")
        
        if updated_sets:
            print(f"\nSets to update ({len(updated_sets)}):")
            for set_data in updated_sets:
                print(f"- {set_data['name']} ({set_data['code']})")
        
        if not new_sets and not updated_sets:
            print("\nAll sets are up to date!")
            return True
        
        # Confirm download
        if not force_download:
            confirm = input("\nProceed with download? (Y/n): ")
            if confirm.lower() == 'n':
                return False
        
        # Download sets
        success = True
        for set_data in new_sets + updated_sets:
            if not self._fetch_set(set_data['code'], set_data):
                success = False
        
        return success
    
    def _fetch_sets_catalog(self, force: bool = False) -> Dict:
        """Get list of all sets from Scryfall"""
        catalog_file = self.cache_dir / "sets_catalog.json"
        
        if not force and catalog_file.exists():
            with open(catalog_file, 'r') as f:
                return json.load(f)
        
        print("Downloading sets catalog...")
        response = requests.get(self.SETS_URL)
        response.raise_for_status()
        
        sets_data = response.json()
        with open(catalog_file, 'w') as f:
            json.dump(sets_data, f, indent=2)
        
        return sets_data
    
    def _fetch_set(self, set_code: str, set_data: Dict) -> bool:
        """Download all cards from a specific set"""
        print(f"\nDownloading {set_data['name']} ({set_code})...")
        
        cache_file = self.sets_dir / f"{set_code}.json"
        search_url = f"{self.BASE_URL}/cards/search?q=set:{set_code}&unique=prints"
        
        try:
            cards = []
            while search_url:
                time.sleep(self.REQUEST_DELAY)
                response = requests.get(search_url)
                
                if response.status_code == 404:
                    print(f"No cards found for set {set_code}")
                    break
                
                response.raise_for_status()
                page_data = response.json()
                
                cards.extend(page_data['data'])
                search_url = page_data.get('next_page')
            
            if cards:
                with open(cache_file, 'w') as f:
                    json.dump(cards, f, indent=2)
                
                self.metadata['sets'][set_code] = {
                    'updated_at': set_data.get('updated_at'),  # Handle missing updated_at
                    'card_count': len(cards),
                    'name': set_data['name']
                }
                self.save_metadata()
                
                print(f"Cached {len(cards)} cards")
                return True
                
        except Exception as e:
            print(f"Error downloading set {set_code}: {e}")
        
        return False
    
    def _filter_sets(self, sets_data: List[Dict]) -> List[Dict]:
        """Filter and sort sets based on criteria"""
        filtered = []
        
        for set_data in sets_data:
            # Skip digital-only sets
            if set_data.get('digital', False):
                continue
                
            # Skip non-paper sets
            if 'paper' not in set_data.get('games', []):
                continue
            
            # Skip art series and other special sets
            if any(x in set_data['name'].lower() for x in ['art series', 'minigame']):
                continue
            
            filtered.append(set_data)
        
        # Sort by release date, newest first
        return sorted(filtered, 
                     key=lambda x: x.get('released_at', '0000-01-01'), 
                     reverse=True)

if __name__ == "__main__":
    collector = ScryfallCollector()
    collector.fetch_all_cards() 