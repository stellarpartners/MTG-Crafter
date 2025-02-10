from pathlib import Path
import shutil
import json
from datetime import datetime
from typing import Tuple, List
import os
import requests
from tqdm import tqdm

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
    print("2. Fresh Start (Download & Compile Everything)")
    print("3. Update Individual Component Cache")
    print("4. Build SQLite Database")
    print("5. Exit")
    
    return input("\nSelect an option (1-5): ")

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
    
    # Remove JSON-related comments and logic
    db = CardDatabase()
    
    if db.needs_update():
        print("Database needs update - rebuilding...")
        db.force_close()
        Path(db.db_path).unlink(missing_ok=True)
        db = CardDatabase()  # Create fresh instance
        
    print(f"Database ready at: {db.db_path}")

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
    
    # Filter sets before processing
    valid_types = [
        'core', 'expansion', 'commander', 'draft_innovation',
        'masters', 'arsenal', 'from_the_vault', 'premium_deck',
        'duel_deck', 'starter', 'box', 'promo', 'token', 'memorabilia',
        'funny', 'planechase', 'archenemy', 'treasure_chest'
    ]
    
    excluded_types = [
        'alchemy', 'minigame', 'masterpiece', 'digital', 
        'art_series', 'vanguard', 'meta', 'augment', 'test'
    ]
    
    # Pre-filter sets
    filtered_sets = [
        s for s in all_sets 
        if s.get('set_type') in valid_types 
        and s.get('set_type') not in excluded_types
        and not any(c in s['code'].lower() for c in ['test', 'tst', 'demo', 'fake', 'pdft', 'pdnt'])
    ]
    
    print(f"\nOriginal set count: {len(all_sets)}")
    print(f"Filtered set count: {len(filtered_sets)}")
    print(f"Excluded {len(all_sets) - len(filtered_sets)} non-card sets")
    
    # Create mapping of normalized set codes to set data
    current_sets = {}
    for s in filtered_sets:  # Use filtered list here
        norm_code = s['code'].lower()
        current_sets[norm_code] = s
        current_sets[norm_code]['file_name'] = f"{s['code']}.json"

    # Find missing and outdated sets
    new_sets = []
    for norm_code, set_data in current_sets.items():
        if norm_code not in existing_sets:
            print(f"New set detected: {set_data['code']}")
            new_sets.append(set_data)
        else:
            existing_file = existing_sets[norm_code]
            try:
                with open(existing_file, 'r') as f:
                    file_data = json.load(f)
                    
                    # Updated validation for older set formats
                    if 'data' not in file_data:
                        raise ValueError("Legacy set format - missing data array")
                        
                    # Handle pagination fields conditionally
                    if file_data.get('has_more', False) and 'next_page' not in file_data:
                        raise ValueError("Missing next_page for paginated set")
                        
                # Handle legacy sets without updated_at
                update_date = set_data.get('updated_at') or set_data.get('released_at')
                if not update_date:
                    raise ValueError("No valid timestamp in set metadata")
                    
                # Rest of date comparison logic...
                file_mtime = datetime.fromtimestamp(existing_file.stat().st_mtime)
                set_update = datetime.fromisoformat(update_date)
                
                if set_update > file_mtime:
                    print(f"Update needed for {set_data['code']}:")
                    print(f"  Set updated: {set_update}")
                    print(f"  File modified: {file_mtime}")
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
        set_url = set_data['search_uri']
        
        try:
            # Skip test sets and invalid codes
            invalid_codes = ['test', 'tst', 'demo', 'fake', 'pdft', 'pdnt']
            if any(c in set_code.lower() for c in invalid_codes):
                print(f"Skipping invalid set: {set_code}")
                continue
                
            # Additional check for set type
            valid_types = [
                'core', 'expansion', 'commander', 'draft_innovation',
                'masters', 'arsenal', 'from_the_vault', 'premium_deck',
                'duel_deck', 'starter', 'box', 'promo', 'token', 'memorabilia',
                'funny', 'planechase', 'archenemy', 'treasure_chest'
            ]
            
            # Explicitly excluded types
            excluded_types = [
                'alchemy', 'minigame', 'masterpiece', 'digital', 
                'art_series', 'vanguard', 'meta', 'augment'
            ]
            
            if set_data.get('set_type') in excluded_types:
                print(f"Skipping excluded set type: {set_code} ({set_data.get('set_type')})")
                continue
            elif set_data.get('set_type') not in valid_types:
                print(f"Skipping unknown set type: {set_code} ({set_data.get('set_type')})")
                continue
                
            # Validate set URL format
            if not set_url.startswith("https://api.scryfall.com/cards/search"):
                print(f"Skipping invalid set URL for {set_code}: {set_url}")
                continue
                
            # Download set data
            response = requests.get(set_url, params={'format': 'json'})
            response.raise_for_status()
            
            # Save to cache
            with open(cache_dir / f"{set_code}.json", 'w') as f:
                json.dump(response.json(), f)
                
        except Exception as e:
            print(f"Error downloading {set_code}: {str(e)}")
            
    # ... existing code to build combined dataset ...

def main():
    """Main program loop"""
    engine = DataEngine()
    
    while True:
        choice = show_main_menu()
        
        if choice == "1":
            print_cache_status(engine)
        elif choice == "2":
            download_scryfall_data(engine)
            engine.cold_start()
        elif choice == "3":
            update_individual_cache(engine)
        elif choice == "4":
            build_sqlite_database(engine)
        elif choice == "5":
            print("Exiting...")
            break
        else:
            print("Invalid choice, please try again")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main() 