from pathlib import Path
import json
import requests
from datetime import datetime
import time
from typing import List, Dict, Optional
from tqdm import tqdm
from collections import defaultdict

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
    
    def fetch_all_cards(self, force_download: bool = False, debug: bool = False) -> bool:
        """Download cards by set with smart caching"""
        print("\nChecking card data...")
        
        # First get sets catalog
        sets_data = self._fetch_sets_catalog(force_download)
        if not sets_data:
            return False
        
        # Get list of all available sets
        available_sets = {
            set_data['code']: set_data 
            for set_data in self._filter_sets(sets_data['data'])
        }
        
        # Get list of what we have
        cached_sets = set()
        for set_file in self.sets_dir.glob("*.json"):
            cached_sets.add(set_file.stem)
        
        # Find missing sets
        missing_sets = set(available_sets.keys()) - cached_sets
        
        # Show status
        print("\nCache Status:")
        print(f"- Available sets: {len(available_sets)}")
        print(f"- Sets in cache: {len(cached_sets)}")
        print(f"- Missing sets: {len(missing_sets)}")
        
        if missing_sets:
            print("\nMissing sets:")
            for set_code in sorted(missing_sets):
                set_data = available_sets[set_code]
                print(f"- {set_data['name']} ({set_code}) - Released: {set_data['released_at']}")
            
            # Confirm download
            if not force_download:
                confirm = input("\nDownload missing sets? (Y/n): ")
                if confirm.lower() == 'n':
                    return False
            
            # Download only missing sets
            success = True
            for set_code in missing_sets:
                if not self._fetch_set(set_code, available_sets[set_code]):
                    success = False
            
            return success
        
        print("\nAll sets are cached!")
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
        """Filter and sort sets based on criteria"""
        print("\nAnalyzing sets from Scryfall:")
        print(f"Total sets from API: {len(sets_data)}")
        
        filtered = []
        skipped_reasons = defaultdict(list)
        
        for set_data in sets_data:
            set_code = set_data['code']
            set_name = set_data['name']
            
            # Debug print for a few sets to see what's happening
            if len(filtered) < 3:
                print(f"\nDebug set data for {set_name}:")
                print(f"- digital: {set_data.get('digital', False)}")
                print(f"- games: {set_data.get('games', [])}")
                print(f"- set_type: {set_data.get('set_type', 'unknown')}")
            
            # Skip digital-only sets
            if set_data.get('digital', False):
                skipped_reasons['digital'].append(f"{set_name} ({set_code})")
                continue
            
            # Skip special sets
            if any(x in set_name.lower() for x in ['art series', 'minigame']):
                skipped_reasons['special'].append(f"{set_name} ({set_code})")
                continue
            
            # Accept all non-digital sets for now
            filtered.append(set_data)
        
        # Sort by release date, newest first
        filtered.sort(key=lambda x: x.get('released_at', '0000-01-01'), reverse=True)
        
        # Print filtering stats
        print("\nFiltering results:")
        print(f"- Total sets: {len(sets_data)}")
        print(f"- Kept sets: {len(filtered)}")
        print("\nSkipped sets:")
        for reason, sets in skipped_reasons.items():
            print(f"- {reason}: {len(sets)} sets")
            if len(sets) < 5:  # Show examples for small groups
                for set_name in sets:
                    print(f"  - {set_name}")
        
        return filtered

if __name__ == "__main__":
    collector = ScryfallCollector()
    collector.fetch_all_cards() 