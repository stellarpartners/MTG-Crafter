from pathlib import Path
import json
import requests
from datetime import datetime
import time
from typing import List, Dict, Optional, TYPE_CHECKING
from tqdm import tqdm
from collections import defaultdict
import re

if TYPE_CHECKING:
    from src.collectors.data_engine import DataEngine

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
        print(f"Creating cache directory: {self.cache_dir}")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.sets_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache files
        self.metadata_file = self.cache_dir / "metadata.json"
        
        self._last_request_time = 0
        self._request_count = 0
        self._request_window = []  # Track requests in last minute
        
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
        """Implement proper rate limiting"""
        current_time = time.time()
        
        # Clean old requests from window
        self._request_window = [t for t in self._request_window 
                              if current_time - t < 60]
        
        # If we've made too many requests recently, wait
        if len(self._request_window) >= 60:  # Scryfall's limit is 60/minute
            sleep_time = 60 - (current_time - self._request_window[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        # Add current request to window
        self._request_window.append(current_time)
        
        # Also respect per-request delay
        time_since_last = current_time - self._last_request_time
        if time_since_last < self.REQUEST_DELAY:
            time.sleep(self.REQUEST_DELAY - time_since_last)
        
        self._last_request_time = time.time()
    
    def _analyze_cache(self):
        """Analyze current cache state"""
        print("\nAnalyzing cache:")
        
        # Check sets directory
        set_files = list(self.sets_dir.glob("*.json"))
        print(f"Found {len(set_files)} set files in cache")
        
        # Check metadata
        if self.metadata_file.exists():
            print(f"Metadata tracks {len(self.metadata['sets'])} sets")
            
            # Compare files vs metadata
            file_codes = {f.stem for f in set_files}
            meta_codes = set(self.metadata['sets'].keys())
            
            missing_meta = file_codes - meta_codes
            missing_files = meta_codes - file_codes
            
            if missing_meta:
                print("\nSets with files but no metadata:")
                for code in sorted(missing_meta):
                    print(f"- {code}")
            
            if missing_files:
                print("\nSets in metadata but missing files:")
                for code in sorted(missing_files):
                    print(f"- {code} ({self.metadata['sets'][code]['name']})")
        else:
            print("No metadata file found")
    
    def fetch_all_cards(self, force_download: bool = False) -> bool:
        print(f"Downloading cards to: {self.sets_dir}")
        sets = self._get_available_sets()
        print(f"Found {len(sets)} valid sets to process")
        
        for set_data in tqdm(sets, desc="Processing sets"):
            self._process_set(set_data, force_download)
        
        print(f"\nCard data collection complete in {self.sets_dir}")
        return True
    
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
        """NO FILTERING - Return all sets"""
        print("\nProcessing sets from Scryfall:")
        print(f"Total sets from API: {len(sets_data)}")
        
        # Remove all filtering logic - just return the sorted list
        filtered = sets_data
        
        # Sort by release date
        filtered.sort(key=lambda x: x['released_at'], reverse=True)
        
        print(f"\nProcessing {len(filtered)} sets total")
        return filtered

    def _get_available_sets(self) -> List[Dict]:
        """Get filtered list of available sets"""
        catalog = self._fetch_sets_catalog()
        return self._filter_sets(catalog.get('data', []))

    def _process_set(self, set_data: Dict, force: bool = False):
        """Process an individual set"""
        set_code = set_data['code']
        cache_file = self.sets_dir / f"{set_code}.json"
        
        print(f"\nProcessing set: {set_data['name']} ({set_code})")
        if not force and cache_file.exists():
            # Check if existing file is valid
            try:
                with open(cache_file, 'r') as f:
                    existing_data = json.load(f)
                    if len(existing_data) > 0:
                        print(f"Using cached {set_code} ({len(existing_data)} cards)")
                        return True
            except:
                pass
        
        if not force and not self.needs_update(set_code, set_data):
            return
        
        print(f"Processing {set_data['name']} ({set_code})...")
        self._fetch_set(set_code, set_data)

    def _process_legacy_set_file(self, file_path: Path) -> bool:
        """Convert legacy set file to new format with validation"""
        try:
            # Read file with error checking
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    legacy_data = json.load(f)
            except json.JSONDecodeError as e:
                print(f"Corrupted JSON in {file_path.name}: {e}")
                return False
            
            # Check if it's a legacy format (no 'data' key)
            if 'data' not in legacy_data:
                print(f"Migrating legacy set file: {file_path.name}")
                
                # Validate card data structure
                if not isinstance(legacy_data, list):
                    print(f"Invalid legacy format in {file_path.name}")
                    return False
                
                # Create new structure
                new_data = {
                    'data': legacy_data,
                    'has_more': False,
                    'next_page': None
                }
                
                # Save with validation
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(new_data, f, indent=2)
                    return True
                except Exception as e:
                    print(f"Error saving migrated file {file_path.name}: {e}")
                    return False
                
        except Exception as e:
            print(f"Error migrating {file_path.name}: {e}")
        
        return False

if __name__ == "__main__":
    collector = ScryfallCollector()
    collector.fetch_all_cards() 