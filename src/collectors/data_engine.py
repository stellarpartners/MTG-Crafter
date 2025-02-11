from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .scryfall import ScryfallCollector
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
from .scryfall import ScryfallCollector
from .banlist_collector import BanlistCollector
from .theme_collectors import ThemeCollector
from .keyword_collector import KeywordCollector
from src.database.card_database import CardDatabase

class DataEngine:
    """Main engine for collecting and managing MTG data"""
    
    def __init__(self, cache_dir: str = "cache", data_dir: str = "data", light_init: bool = False):
        # Set up directories
        self.cache_dir = Path(cache_dir)
        self.data_dir = Path(data_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create database
        print("Initializing database...")
        self.database = CardDatabase()
        print(f"DataEngine: CardDatabase object ID: {id(self.database)}")
        
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
        """Check if we have valid cached card data"""
        # Simplify to just check sets catalog
        catalog_path = self.cache_dir / "scryfall/sets_catalog.json"
        return catalog_path.exists()
    
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

    def cold_start(self):
        """Fresh initialization sequence"""
        print("=== Cold Start Initialization ===")
        
        # Phase 1: Database population 
        print("\n1. Building database...")
        self.database = CardDatabase()  # Creates fresh instance
        
        # Phase 2: Core card data (only if missing)
        if self._has_card_cache() and not self.database.needs_update():
            print("\n2. Using existing card data")
        else:
            print("\n2. Downloading card data...")
            self.scryfall.fetch_all_cards(force_download=False)  # Only get new/missing sets
        
        # Phase 3: Supplemental data
        print("\n3. Collecting supplemental data...")
        self.banlist.fetch_banned_cards()
        self.themes.update_all() 
        self.keywords.download_rules()
        
        print("\nSystem ready!")

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

    def _filter_sets(self, all_sets):
        # Return all sets without any filtering
        return all_sets

if __name__ == "__main__":
    engine = DataEngine()
    
    # For first time setup
    engine.cold_start()
    
    # For regular updates
    # engine.update_if_needed() 