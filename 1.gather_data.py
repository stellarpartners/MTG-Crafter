from pathlib import Path
import shutil
import json
from datetime import datetime
from typing import Tuple, List
import os
import requests
from tqdm import tqdm
import time

from src.collectors.data_engine import DataEngine
from src.database.card_database import CardDatabase

def print_header():
    print("MTG Crafter - Data Management Tool")
    print("==================================")

def show_main_menu():
    """Display main menu and handle input"""
    print("\nMTG Crafter - Data Management Tool")
    print("==================================")
    print("\nMain Menu:")
    print("1. Show Cache Status")
    print("2. Update All Data")
    print("3. Update Individual Component Cache")
    print("4. Build SQLite Database")
    print("5. Delete Database")
    print("6. Exit")
    
    return input("\nSelect an option (1-6): ")

def show_update_menu():
    print("\nUpdate Component Cache:")
    print("1. Download New/Updated Sets")
    print("2. Update Banlists")
    print("3. Update Rules")
    print("4. Update Themes")
    print("5. Update Everything")
    print("6. Back to Main Menu")
    return input("\nSelect an option (1-6): ")

def validate_cache(engine: DataEngine) -> Tuple[bool, List[str]]:
    """Validate all cache files"""
    issues = []
    
    # Simplified Scryfall check
    sets_dir = engine.cache_dir / "scryfall/sets"
    if not sets_dir.exists():
        issues.append("Missing Scryfall sets directory")
    else:
        set_count = len(list(sets_dir.glob("*.json")))
        print(f"- Found {set_count} cached sets")
    
    # Remove JSON validation checks
    return len(issues) == 0, issues

def print_cache_status(engine: DataEngine):
    """Display current cache status"""
    print("\nChecking cache status...")
    
    # Check Scryfall sets
    sets_dir = engine.cache_dir / "scryfall/sets"
    if sets_dir.exists():
        set_files = list(sets_dir.glob("*.json"))
        print(f"\nScryfall cache:")
        print(f"- Found {len(set_files)} set files")
        
        # Check a few recent sets
        recent_sets = sorted(set_files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]
        if recent_sets:
            print("\nMost recently updated sets:")
            for set_file in recent_sets:
                mtime = datetime.fromtimestamp(set_file.stat().st_mtime)
                print(f"- {set_file.stem} (Updated: {mtime.strftime('%Y-%m-%d %H:%M')})")
    
    # Check banlists
    banlist_file = engine.cache_dir / "banlists/banlists.json"
    print("\nBanlists:")
    if banlist_file.exists():
        mtime = datetime.fromtimestamp(banlist_file.stat().st_mtime)
        print(f"- Last updated: {mtime.strftime('%Y-%m-%d %H:%M')}")
    else:
        print("- Not downloaded")
    
    # Check rules
    rules_file = engine.cache_dir / "rules/MagicCompRules.txt"
    print("\nRules:")
    if rules_file.exists():
        mtime = datetime.fromtimestamp(rules_file.stat().st_mtime)
        print(f"- Last updated: {mtime.strftime('%Y-%m-%d %H:%M')}")
    else:
        print("- Not downloaded")
    
    # Check themes
    themes_file = engine.cache_dir / "themes/edhrec/themes.json"
    print("\nThemes:")
    if themes_file.exists():
        mtime = datetime.fromtimestamp(themes_file.stat().st_mtime)
        print(f"- Last updated: {mtime.strftime('%Y-%m-%d %H:%M')}")
    else:
        print("- Not downloaded")

def build_sqlite_database(engine: DataEngine):
    """Build SQLite database from collected data"""
    print("\nBuilding SQLite database...")
    
    # Force rebuild
    engine.database.force_close()
    engine.database.create_tables()
    engine.database.load_data()  # This will now load from JSON files
    
    # Verification
    db = engine.database
    cursor = db.conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    print("\nDatabase tables:", [row[0] for row in cursor.fetchall()])
    
    cursor = db.conn.execute("SELECT COUNT(*) FROM cards")
    print("Total cards:", cursor.fetchone()[0])

    # After building database
    db_path = Path("data/database/cards.db")
    print(f"Database size: {db_path.stat().st_size / 1024:.1f} KB")

def update_individual_cache(engine: DataEngine):
    """Update individual cache components"""
    while True:
        choice = show_update_menu()
        
        if choice == "1":
            print("\nUpdating sets...")
            engine.scryfall.fetch_all_cards(force_download=True)
        elif choice == "2":
            print("\nUpdating banlists...")
            engine.banlist.fetch_banned_cards()
        elif choice == "3":
            print("\nUpdating rules...")
            engine.keywords.download_rules()
        elif choice == "4":
            print("\nUpdating themes...")
            engine.themes.update_all()
        elif choice == "5":
            print("\nUpdating everything...")
            engine.update_if_needed()
        elif choice == "6":
            return
        else:
            print("\nInvalid choice")
        
        input("\nPress Enter to continue...")

def download_scryfall_data(engine: DataEngine):
    """Download missing Scryfall sets using DataEngine's configuration"""
    cache_dir = engine.scryfall.sets_dir
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Get list of existing sets with their stems (set codes)
    existing_sets = {}
    for f in cache_dir.glob("*.json"):
        if f.stem == "all_cards":
            continue
        try:
            # Extract set code from file name (case-insensitive)
            existing_sets[f.stem.lower()] = f
        except:
            continue

    # Get current set list from Scryfall
    sets_url = "https://api.scryfall.com/sets"
    all_sets = requests.get(sets_url).json()['data']
    
    # Use all sets, no filtering
    current_sets = {}
    for s in all_sets:
        norm_code = s['code'].lower()
        current_sets[norm_code] = s
        current_sets[norm_code]['file_name'] = f"{s['code']}.json"
    print(f"\nTotal sets from Scryfall: {len(all_sets)}")

    # Find missing and outdated sets
    new_sets = []
    for norm_code, set_data in current_sets.items():
        if norm_code not in existing_sets:
            print(f"New set detected: {set_data['code']}")
            new_sets.append(set_data)
        else:
            existing_file = existing_sets[norm_code]
            try:
                # Check if file needs migration/updating
                with open(existing_file, 'r') as f:
                    file_data = json.load(f)
                
                if 'data' not in file_data:
                    if engine.scryfall._process_legacy_set_file(existing_file):
                        print(f"Migrated legacy set: {existing_file.name}")
                        with open(existing_file, 'r') as f:
                            file_data = json.load(f)
                    else:
                        raise ValueError("Failed to migrate legacy set")
                
                if 'data' not in file_data:
                    raise ValueError("Invalid set format after migration")
                
                update_date = set_data.get('updated_at') or set_data.get('released_at')
                if not update_date:
                    raise ValueError("No valid timestamp in set metadata")
                
                set_update = datetime.fromisoformat(update_date.replace('Z', '+00:00'))
                file_mtime = datetime.fromtimestamp(existing_file.stat().st_mtime)

                if set_update > file_mtime:
                    print(f"Update needed for {set_data['code']}:")
                    print(f"  Set updated: {set_update.strftime('%Y-%m-%d %H:%M')}")
                    print(f"  File modified: {file_mtime.strftime('%Y-%m-%d %H:%M')}")
                    new_sets.append(set_data)
                    existing_file.unlink()
                else:
                    print(f"{set_data['code']} is up-to-date")
            except Exception as e:
                print(f"Validation failed for {existing_file.name}: {str(e)}")
                new_sets.append(set_data)
                existing_file.unlink()

    print(f"\nSet Status:")
    print(f"- Total sets available: {len(all_sets)}")
    print(f"- Already cached: {len(existing_sets)}")
    print(f"- New/updated sets: {len(new_sets)}")

    if not new_sets:
        print("\nAll sets are up-to-date!")
        return

    print(f"Downloading {len(new_sets)} missing sets...")
    
    for set_data in tqdm(new_sets, desc="Downloading sets"):
        set_code = set_data['code']
        try:
            # Get complete set metadata
            set_meta_url = f"https://api.scryfall.com/sets/{set_code.lower()}"
            meta_response = requests.get(set_meta_url)
            meta_response.raise_for_status()
            set_metadata = meta_response.json()

            # Get all cards with pagination
            all_cards = []
            cards_url = set_metadata.get('search_uri')
            if not cards_url:
                print(f"Skipping {set_code} - no valid search URI")
                continue

            while cards_url:
                response = requests.get(cards_url, params={'format': 'json'})
                response.raise_for_status()
                data = response.json()
                all_cards.extend(data.get('data', []))
                cards_url = data.get('next_page')
                time.sleep(0.1)  # Respect rate limits

            # Build complete dataset
            combined_data = {
                'object': 'set',
                'code': set_metadata.get('code', '').upper(),
                'name': set_metadata.get('name', 'Unknown Set'),
                'released_at': set_metadata.get('released_at'),
                'set_type': set_metadata.get('set_type', 'unknown'),
                'card_count': len(all_cards),
                'data': all_cards
            }

            # Validate structure before saving
            if not isinstance(combined_data.get('data'), list):
                raise ValueError("Invalid card data format")

            # Save with atomic write
            temp_path = cache_dir / f"{set_code}.tmp"
            with open(temp_path, 'w') as f:
                json.dump(combined_data, f, indent=2)
            
            # Replace existing file atomically
            final_path = cache_dir / f"{set_code}.json"
            temp_path.replace(final_path)

        except Exception as e:
            print(f"Failed to download {set_code}: {str(e)}")
            continue

def main():
    """Main program loop"""
    engine = DataEngine()
    
    while True:
        choice = show_main_menu()
        
        if choice == "1":
            print_cache_status(engine)
        elif choice == "2":
            engine.update_if_needed()
        elif choice == "3":
            update_individual_cache(engine)
        elif choice == "4":
            build_sqlite_database(engine)
        elif choice == "5":
            print("\nDeleting database...")
            engine.database.force_close()
            try:
                Path(engine.database.db_path).unlink()
                print("Database deleted successfully")
            except Exception as e:
                print(f"Error deleting database: {e}")
        elif choice == "6":
            print("Exiting...")
            break
        else:
            print("Invalid choice, please try again")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()

# After running "Update All Data" and "Build SQLite Database"
# Check cache directory
cache_dir = Path("cache/scryfall/sets")
print(f"Set files: {len(list(cache_dir.glob('*.json')))}") 