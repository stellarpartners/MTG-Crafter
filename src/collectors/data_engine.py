from datetime import datetime, timedelta
from pathlib import Path
import json
from typing import Dict, Optional, List
import sys
from os.path import dirname, abspath
import time

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
        
        # Initialize database
        self.database = CardDatabase(self.data_dir / "database" / "cards.db")
        
        # Initialize collectors
        self.scryfall = ScryfallCollector(
            cache_dir=str(self.cache_dir / "scryfall")
        )
        self.banlist = BanlistCollector(
            cache_dir=str(self.cache_dir / "banlists"),
            data_dir=str(self.data_dir / "banlists")
        )
        self.themes = ThemeCollector(
            cache_dir=str(self.cache_dir / "themes"),
            data_dir=str(self.data_dir / "themes")
        )
        self.keywords = KeywordCollector(
            cache_dir=str(self.cache_dir / "keywords"),
            data_dir=str(self.data_dir / "keywords")
        )
        
        # Engine metadata
        self.metadata_file = self.data_dir / "metadata.json"
        self.load_metadata()
        
        if True: # Always initialize collectors
            self._initialize_collectors()
    
    def _initialize_collectors(self):
        """Initialize all collectors"""
        try:
            # Initialize collectors
            self.scryfall = ScryfallCollector(
                cache_dir=str(self.cache_dir / "scryfall")
            )
            
            self.database = CardDatabase(str(self.data_dir / "cards.json"))
            
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
        except Exception as e:
            print(f"Error initializing collectors: {e}")
            raise
    
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
            try:
                with open(self.metadata_file, 'r') as f:
                    self.metadata = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError) as e:
                print(f"Error loading metadata: {e}. Using default metadata.")
                self.metadata = default_metadata
                self.save_metadata()
                return
                
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
    
    def _validate_cache_file(self, path: Path, required_fields: List[str] = None, is_list: bool = False) -> bool:
        """Validate a cache file for JSON format and required fields"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Handle both list and dictionary structures
                if is_list:
                    if not isinstance(data, (list, dict)):
                        print(f"Invalid cache structure in {path.name}: Expected list or dict")
                        return False
                    
                    # If it's a dictionary, check if it has a 'data' key
                    if isinstance(data, dict) and 'data' in data:
                        data = data['data']
                    
                    if not isinstance(data, list):
                        print(f"Invalid cache structure in {path.name}: Expected list")
                        return False
                
                if required_fields:
                    # Check required fields in the first item if it's a list
                    if is_list and data:
                        if not all(field in data[0] for field in required_fields):
                            print(f"Missing required fields in {path.name}")
                            return False
                    # Check required fields directly if it's a dictionary
                    elif not is_list and not all(field in data for field in required_fields):
                        print(f"Missing required fields in {path.name}")
                        return False
                
                return True
                
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Invalid JSON in {path.name}: {str(e)}")
            return False
        except Exception as e:
            print(f"Error validating {path.name}: {str(e)}")
            return False

    def _has_card_cache(self) -> bool:
        """Check if we have a valid cached card data"""
        cache_files = {
            'sets': (self.cache_dir / "scryfall/sets_catalog.json", ['code', 'name'], True),
            'cards': (self.cache_dir / "scryfall/all_cards.json", ['name', 'scryfall_uri'], True)
        }
        
        return all(self._validate_cache_file(path, required_fields, is_list) for path, required_fields, is_list in cache_files.values())
    
    def _download_data(self, collector_type: str) -> bool:
        """Download data for a specific collector"""
        try:
            if collector_type == 'banlists':
                print("\nDownloading banlists...")
                success = self.banlist.fetch_banned_cards()
            elif collector_type == 'rules':
                print("\nDownloading rules...")
                success = self.keywords.download_rules()
            elif collector_type == 'themes':
                print("\nDownloading themes...")
                success = self.themes.update_all()
            else:
                print(f"Invalid collector type: {collector_type}")
                return False
            
            if success:
                self.metadata['last_updates'][collector_type] = datetime.now().isoformat()
                print(f"{collector_type.capitalize()} downloaded successfully")
                return True
            else:
                print(f"Failed to download {collector_type}")
                return False
            
        except Exception as e:
            print(f"Warning: Failed to download {collector_type}: {e}")
            return False

    def cold_start(self, force_download: bool = False):
        """Initialize all data collections in stages"""
        print("Starting MTG Crafter data engine...")
        
        # Stage 1: Card Data Download
        print("\n=== Stage 1: Card Data Download ===")
        print("\n1. Downloading card data from Scryfall...")
        self.scryfall = ScryfallCollector(
            cache_dir=str(self.cache_dir / "scryfall")
        )
        if not self.scryfall.fetch_all_cards(force_download=force_download):
            print("Failed to download card data!")
            return False
        
        # Stage 2: Additional Data Collection
        print("\n=== Stage 2: Additional Data Collection ===")
        
        for collector_type in ['banlists', 'rules', 'themes']:
            self._download_data(collector_type)
        
        self.save_metadata()
        print("\nData engine initialization complete!")
        return True

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
        print("1. Download New Sets")
        print("2. Update Banlists")
        print("3. Update Rules")
        print("4. Update Themes")
        print("5. Update Everything")
        print("6. Back to Main Menu")
        return input("\nSelect an option (1-6): ")

    def _update_collector(self, collector_type: str, force: bool = False) -> bool:
        """Update a specific collector if needed"""
        try:
            if collector_type == 'sets':
                print("\nUpdating card data...")
                return self.scryfall.fetch_all_cards(force_download=force)
            else:
                return self._download_data(collector_type)
            
        except Exception as e:
            print(f"Error updating {collector_type}: {e}")
            return False

    def _needs_update(self, collector_type: str) -> bool:
        """Check if a collector needs updating based on metadata"""
        try:
            if collector_type == 'sets':
                return self.scryfall.needs_update()
            elif collector_type == 'themes':
                return self.themes.needs_update()
            elif collector_type == 'rules':
                return self.keywords.needs_update()
            return False
        except Exception:
            return True

    def update_if_needed(self, collector_type: str = None):
        """Update specific or all collectors"""
        if collector_type:
            success = self._update_collector(collector_type)
            if success:
                self.save_metadata()
        else:
            # Update everything
            for collector in ['sets', 'banlists', 'rules', 'themes']:
                if self._update_collector(collector):
                    self.save_metadata()

    def cleanup(self):
        """Close all connections and clean up resources"""
        if self.database:
            try:
                self.database.force_close()
            except Exception as e:
                print(f"Error closing database: {e}")
        if hasattr(self, "conn"):
            self.conn = None

class CardDatabase:
    """Card database to load and search card information"""
    def __init__(self, json_file_path: str):
        print(f"[DEBUG] Initializing CardDatabase with path: {json_file_path}")  # Debug
        self.json_file_path = json_file_path
        self.cards = {}
        self.is_loaded = False  # Initialize is_loaded attribute
        self.load_data()
    
    def load_data(self):
        """Load card data from JSON file"""
        print(f"[DEBUG] Loading data from: {self.json_file_path}")  # Debug
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.cards = {card['name']: card for card in data}
                self.is_loaded = True  # Set is_loaded to True if successful
                print(f"[DEBUG] Loaded {len(self.cards)} cards from {self.json_file_path}")  # Debug
        except FileNotFoundError:
            print(f"[DEBUG] Error: Card database file not found at {self.json_file_path}")  # Debug
            self.is_loaded = False  # Set is_loaded to False if file not found
        except json.JSONDecodeError:
            print(f"[DEBUG] Error: Could not decode JSON from {self.json_file_path}")  # Debug
            self.is_loaded = False  # Set is_loaded to False if JSON decode fails
        except Exception as e:
            print(f"[DEBUG] Error loading card database: {str(e)}")  # Debug
            self.is_loaded = False  # Set is_loaded to False for any other errors
    
    def get_card(self, card_name: str) -> Dict:
        """Get card information by name"""
        return self.cards.get(card_name)
    
    def needs_update(self, cache_dir: Path) -> bool:
        """Check if the database needs updating based on cache files"""
        # Check if the cache directory exists and has the necessary files
        if not cache_dir.exists():
            return True
        return False
    
    def close(self):
        """Close the database connection"""
        pass  # No connection to close in this implementation

if __name__ == "__main__":
    engine = DataEngine()
    
    # For first time setup
    engine.cold_start()
    
    # For regular updates
    # engine.update_if_needed() 