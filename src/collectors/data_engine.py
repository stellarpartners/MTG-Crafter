from datetime import datetime, timedelta
from pathlib import Path
import json
from typing import Dict, Optional
import sys
from os.path import dirname, abspath

# Add src to Python path for imports
root_dir = dirname(dirname(dirname(abspath(__file__))))
sys.path.append(root_dir)

# Change relative imports to absolute
from src.collectors.scryfall import ScryfallCollector
from src.collectors.banlist_collector import BanlistCollector
from src.collectors.theme_collectors import ThemeCollector
from src.collectors.keyword_collector import KeywordCollector
from src.database.card_database import CardDatabase

class DataEngine:
    """Main engine for collecting and managing MTG data"""
    
    def __init__(self, cache_dir: str = "cache", data_dir: str = "data"):
        # Set up directories
        self.cache_dir = Path(cache_dir)
        self.data_dir = Path(data_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Engine metadata
        self.metadata_file = self.data_dir / "metadata.json"
        self.load_metadata()
        
        # Initialize collectors
        self.scryfall = ScryfallCollector(
            cache_dir=str(self.cache_dir / "scryfall"),
            data_dir=str(self.data_dir / "database")
        )
        self.database = self.scryfall.database
        self.banlist = BanlistCollector(
            cache_dir=str(self.cache_dir / "banlists"),
            data_dir=str(self.data_dir / "banlists")
        )
        self.themes = ThemeCollector(
            cache_dir=str(self.cache_dir / "themes"),
            data_dir=str(self.data_dir / "themes")
        )
        self.keywords = KeywordCollector(data_dir=str(self.cache_dir / "keywords"))
    
    def load_metadata(self):
        """Load or initialize engine metadata"""
        default_metadata = {
            'last_updates': {
                'sets': None,
                'banlists': None,
                'themes': None,
                'keywords': None,
                'rules': None
            },
            'update_frequencies': {
                'sets': 90,      # Days between set updates
                'banlists': 30,  # Days between banlist updates
                'themes': 7,     # Days between theme updates
                'keywords': 90,  # Days between keyword updates
                'rules': 90      # Days between rules updates
            }
        }
        
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                self.metadata = json.load(f)
                
            # Ensure all required keys exist
            for section in default_metadata:
                if section not in self.metadata:
                    self.metadata[section] = {}
                for key in default_metadata[section]:
                    if key not in self.metadata[section]:
                        self.metadata[section][key] = default_metadata[section][key]
            
            self.save_metadata()  # Save any added keys
        else:
            self.metadata = default_metadata
            self.save_metadata()
    
    def save_metadata(self):
        """Save engine metadata"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def cold_start(self, force_download: bool = False):
        """Initialize all data collections in stages"""
        print("Starting MTG Crafter data engine...")
        
        # Stage 1: Card Data
        print("\n=== Stage 1: Card Data ===")
        if force_download or not self._has_card_cache():
            print("Downloading fresh card data from Scryfall...")
            self.scryfall.fetch_all_cards(force_download=True)
        else:
            print("Using cached card data...")
            self.scryfall.fetch_all_cards(force_download=False)
        
        # Stage 2: Additional Data
        if self.database.cards:  # Only proceed if we have card data
            print("\n=== Stage 2: Additional Data ===")
            
            print("\n1. Processing banned cards...")
            try:
                self.banlist.fetch_banned_cards()
                self.metadata['last_updates']['banlists'] = datetime.now().isoformat()
            except Exception as e:
                print(f"Warning: Failed to fetch banned cards: {e}")
            
            print("\n2. Processing themes...")
            try:
                self.themes.update_all()
                self.metadata['last_updates']['themes'] = datetime.now().isoformat()
            except Exception as e:
                print(f"Warning: Failed to collect themes: {e}")
            
            print("\n3. Processing keywords...")
            try:
                self.keywords.collect_keywords_from_cards()
                self.keywords.extract_ability_words()
                self.keywords.enrich_keywords()
                self.metadata['last_updates']['keywords'] = datetime.now().isoformat()
            except Exception as e:
                print(f"Warning: Failed to process keywords: {e}")
        
        self.save_metadata()
        print("\nData engine initialization complete!")

    def _has_card_cache(self) -> bool:
        """Check if we have cached card data"""
        cache_status = self.scryfall._check_cache()
        return cache_status.exists
    
    def needs_update(self, collector_type: str) -> bool:
        """Check if a collector needs updating"""
        # Ensure the collector type exists in metadata
        if collector_type not in self.metadata['last_updates']:
            self.metadata['last_updates'][collector_type] = None
            self.save_metadata()
            return True
            
        last_update = self.metadata['last_updates'][collector_type]
        if not last_update:
            return True
            
        last_update_date = datetime.fromisoformat(last_update)
        frequency = timedelta(days=self.metadata['update_frequencies'][collector_type])
        return datetime.now() - last_update_date > frequency
    
    def update_if_needed(self, collector_type: str = None):
        """Update specific or all collectors if needed"""
        if collector_type:
            self._update_collector(collector_type)
        else:
            for collector in ['sets', 'banlists', 'themes', 'keywords', 'rules']:
                self._update_collector(collector)
    
    def _update_collector(self, collector_type: str):
        """Update a specific collector if needed"""
        if not self.needs_update(collector_type):
            print(f"{collector_type} data is up to date")
            return
            
        print(f"\nUpdating {collector_type}...")
        if collector_type == 'sets':
            self.scryfall.fetch_standard_sets()
        elif collector_type == 'banlists':
            self.banlist.fetch_banned_cards()
        elif collector_type == 'themes':
            self.themes.update_all()
        elif collector_type == 'keywords':
            self.keywords.collect_keywords_from_cards()
            self.keywords.enrich_keywords()
        elif collector_type == 'rules':
            if self.keywords.download_rules():
                print("Rules updated successfully")
            else:
                print("Failed to update rules")
                return
            
        self.metadata['last_updates'][collector_type] = datetime.now().isoformat()
        self.save_metadata()
        print(f"{collector_type} update complete!")

if __name__ == "__main__":
    engine = DataEngine()
    
    # For first time setup
    engine.cold_start()
    
    # For regular updates
    # engine.update_if_needed() 