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
    
    def __init__(self, cache_dir: str = "cache", data_dir: str = "data", light_init: bool = False):
        # Set up directories
        self.cache_dir = Path(cache_dir)
        self.data_dir = Path(data_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Engine metadata
        self.metadata_file = self.data_dir / "metadata.json"
        self.load_metadata()
        
        # Initialize collectors without loading database
        self.scryfall = None
        self.database = None
        self.banlist = None
        self.themes = None
        self.keywords = None
        
        if not light_init:
            self._initialize_collectors()
    
    def _initialize_collectors(self):
        """Initialize all collectors"""
        try:
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
            self.keywords = KeywordCollector(
                cache_dir=str(self.cache_dir / "rules"),
                data_dir=str(self.data_dir / "keywords")
            )
        except json.JSONDecodeError:
            # If we can't load the database, it's probably because we need a fresh start
            print("Database not found or corrupted. Please use Fresh Start to download data.")
            return
    
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
    
    def _has_card_cache(self) -> bool:
        """Check if we have a valid cached card data"""
        cache_files = {
            'bulk_data': self.cache_dir / "scryfall/bulk_cards_cache.json",
            'metadata': self.cache_dir / "scryfall/bulk_cache_metadata.json"
        }
        
        for path in cache_files.values():
            if not path.exists():
                return False
            try:
                # Validate JSON format and basic structure
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Validate bulk data structure
                    if path.name == "bulk_cards_cache.json":
                        if not isinstance(data, list):
                            print(f"Invalid cache structure in {path.name}: Expected list of cards")
                            return False
                        if not data:  # Empty list
                            print(f"Empty card data in {path.name}")
                            return False
                        # Check first card has required fields
                        required_fields = ['name', 'id', 'oracle_id']
                        if not all(field in data[0] for field in required_fields):
                            print(f"Missing required fields in {path.name}")
                            return False
                    
                    # Validate metadata structure
                    if path.name == "bulk_cache_metadata.json":
                        required_fields = ['downloaded_at', 'last_updated', 'card_count']
                        if not all(field in data for field in required_fields):
                            print(f"Missing required metadata fields in {path.name}")
                            return False
                    
            except json.JSONDecodeError as e:
                print(f"Invalid JSON in {path.name}: {str(e)}")
                return False
            except Exception as e:
                print(f"Error validating {path.name}: {str(e)}")
                return False
            
        return True
    
    def cold_start(self, force_download: bool = False):
        """Initialize all data collections in stages"""
        print("Starting MTG Crafter data engine...")
        
        # Stage 1: Card Data
        print("\n=== Stage 1: Card Data ===")
        if force_download or not self._has_card_cache():
            if not force_download:
                print("Cache is invalid or corrupted. Forcing fresh download...")
            print("Downloading fresh card data from Scryfall...")
            # Initialize just the Scryfall collector for download
            self.scryfall = ScryfallCollector(
                cache_dir=str(self.cache_dir / "scryfall"),
                data_dir=str(self.data_dir / "database"),
                skip_load=True
            )
            cards = self.scryfall.fetch_all_cards(force_download=True)
            
            # Now initialize the database with the downloaded cards
            self.database = CardDatabase(data_dir=str(self.data_dir / "database"))
            self.database.update_from_scryfall(cards)
            
            # Update scryfall collector with the new database
            self.scryfall.database = self.database
        
        # Now initialize other collectors
        self.banlist = BanlistCollector(
            cache_dir=str(self.cache_dir / "banlists"),
            data_dir=str(self.data_dir / "banlists")
        )
        self.themes = ThemeCollector(
            cache_dir=str(self.cache_dir / "themes"),
            data_dir=str(self.data_dir / "themes")
        )
        self.keywords = KeywordCollector(
            cache_dir=str(self.cache_dir / "rules"),
            data_dir=str(self.data_dir / "keywords")
        )
        
        # Stage 2: Additional Data
        if self.database and self.database.cards:
            print("\n=== Stage 2: Additional Data ===")
            
            print("\n1. Downloading rules...")
            try:
                if self.keywords.download_rules():
                    print("Rules downloaded successfully")
                    self.metadata['last_updates']['rules'] = datetime.now().isoformat()
                else:
                    print("Failed to download rules")
            except Exception as e:
                print(f"Warning: Failed to download rules: {e}")
            
            print("\n2. Processing banned cards...")
            try:
                self.banlist.fetch_banned_cards()
                self.metadata['last_updates']['banlists'] = datetime.now().isoformat()
            except Exception as e:
                print(f"Warning: Failed to fetch banned cards: {e}")
            
            print("\n3. Downloading and processing themes...")
            try:
                self.themes.update_all()
                self.metadata['last_updates']['themes'] = datetime.now().isoformat()
            except Exception as e:
                print(f"Warning: Failed to collect themes: {e}")
            
            print("\n4. Processing keywords...")
            try:
                self.keywords.collect_keywords_from_cards()
                self.keywords.extract_ability_words()
                self.keywords.enrich_keywords()
                self.metadata['last_updates']['keywords'] = datetime.now().isoformat()
            except Exception as e:
                print(f"Warning: Failed to process keywords: {e}")
        
        self.save_metadata()
        print("\nData engine initialization complete!")

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
    
    def show_update_menu():
        print("\nUpdate Component Cache:")
        print("1. Redownload Card Data")
        print("2. Redownload Rules")
        print("3. Redownload Themes")
        print("4. Redownload Everything")
        print("5. Back to Main Menu")
        return input("\nSelect an option (1-5): ")

    def _update_collector(self, collector_type: str):
        """Force update a specific collector by clearing its cache first"""
        print(f"\nUpdating {collector_type}...")
        
        if collector_type == 'sets':
            # Clear Scryfall cache
            cache_files = [
                self.cache_dir / "scryfall/bulk_cards_cache.json",
                self.cache_dir / "scryfall/bulk_cache_metadata.json"
            ]
            for file in cache_files:
                if file.exists():
                    print(f"Removing {file}")
                    file.unlink()
            self.scryfall.fetch_all_cards(force_download=True)
            
        elif collector_type == 'rules':
            rules_file = self.cache_dir / "rules/MagicCompRules.txt"
            if rules_file.exists():
                print(f"Removing {rules_file}")
                rules_file.unlink()
            if self.keywords.download_rules():
                print("Rules updated successfully")
            else:
                print("Failed to update rules")
            return
            
        elif collector_type == 'themes':
            theme_cache = self.cache_dir / "themes/edhrec/themes_raw.json"
            if theme_cache.exists():
                print(f"Removing {theme_cache}")
                theme_cache.unlink()
            self.themes.update_all()
            
        self.metadata['last_updates'][collector_type] = datetime.now().isoformat()
        self.save_metadata()
        print(f"{collector_type} update complete!")

    def update_if_needed(self, collector_type: str = None):
        """Update specific or all collectors"""
        if collector_type:
            self._update_collector(collector_type)
        else:
            # Update everything
            for collector in ['sets', 'rules', 'themes']:
                self._update_collector(collector)

if __name__ == "__main__":
    engine = DataEngine()
    
    # For first time setup
    engine.cold_start()
    
    # For regular updates
    # engine.update_if_needed() 