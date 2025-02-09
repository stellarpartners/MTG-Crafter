from pathlib import Path
import shutil
import json
from datetime import datetime
from typing import Tuple, List
import os

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
    
    # Check Scryfall sets
    print("\nChecking Scryfall cache:")
    sets_dir = engine.cache_dir / "scryfall/sets"
    sets_catalog = engine.cache_dir / "scryfall/sets_catalog.json"
    
    if not sets_dir.exists():
        issues.append("Missing Scryfall sets directory")
    else:
        set_files = list(sets_dir.glob("*.json"))
        set_count = len(set_files)
        print(f"- Found {set_count} sets in {sets_dir}")
        if set_count == 0:
            issues.append("No set files found")
        else:
            # Sample check a few sets
            for set_file in set_files[:3]:
                try:
                    with open(set_file, 'r', encoding='utf-8') as f:
                        json.load(f)  # Validate JSON
                except Exception as e:
                    issues.append(f"Invalid set file {set_file.name}: {e}")
    
    if not sets_catalog.exists():
        issues.append("Missing sets catalog")
    else:
        print(f"- Found sets catalog")
        try:
            with open(sets_catalog, 'r', encoding='utf-8') as f:
                catalog = json.load(f)
                print(f"- Catalog contains {len(catalog.get('data', []))} sets")
        except Exception as e:
            issues.append(f"Invalid sets catalog: {e}")
    
    # Check banlists
    print("\nChecking banlists:")
    banlist_file = engine.cache_dir / "banlists/banlists.json"
    if not banlist_file.exists():
        print(f"- Note: Recommended file missing: {banlist_file}")
    else:
        print(f"- Found banlist data")
    
    # Check themes cache
    print("\nChecking themes:")
    themes_file = engine.cache_dir / "themes/edhrec/themes.json"
    if not themes_file.exists():
        print(f"- Note: Recommended file missing: {themes_file}")
    else:
        print(f"- Found themes data")
    
    # Check rules cache
    print("\nChecking rules:")
    rules_file = engine.cache_dir / "rules/MagicCompRules.txt"
    if not rules_file.exists():
        print(f"- Note: Recommended file missing: {rules_file}")
    else:
        print(f"- Found rules data")
    
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
    """Build or update SQLite database from raw cache"""
    print("\nBuilding SQLite database...")
    
    # Initialize database with proper path
    db_path = engine.data_dir / "database" / "cards.db"
    db = engine.database  # Use the database from the engine
    
    try:
        # Check if we need to update
        if not db.needs_update(engine.cache_dir):
            print("\nDatabase is already up to date!")
            return
        
        # Load cards directly from Scryfall cache
        print("\nLoading cards from Scryfall cache...")
        engine.scryfall.fetch_all_cards(force_download=False)
        
        # Process and load cards into database
        print("\nProcessing cards into database...")
        db.load_from_cache(engine.cache_dir)
        
        # Get count of cards in database
        cursor = db.conn.execute("SELECT COUNT(*) FROM cards")
        count = cursor.fetchone()[0]
        print(f"\nSuccessfully loaded {count} unique cards into database!")
        print(f"Database location: {db_path.resolve()}")
        
    except Exception as e:
        print(f"\nError building database: {e}")
    finally:
        db.close()

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

def main():
    """Main program loop"""
    engine = DataEngine()
    
    while True:
        choice = show_main_menu()
        
        if choice == "1":
            print_cache_status(engine)
        elif choice == "2":
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