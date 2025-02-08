from pathlib import Path
import shutil
import json
from datetime import datetime
from typing import Tuple, List

from src.collectors.data_engine import DataEngine
from src.database.card_database import CardDatabase

def print_header():
    print("MTG Crafter - Data Management Tool")
    print("==================================")

def show_main_menu():
    print("\nMain Menu:")
    print("1. Show Cache Status")
    print("2. Fresh Start (Download & Compile Everything)")
    print("3. Update Individual Component Cache")
    print("4. Rebuild from Cache (Delete processed data & recompile)")
    print("5. Cache Maintenance")
    print("6. View Card Data")
    print("7. Build SQLite Database")
    print("8. Exit")
    return input("\nSelect an option (1-8): ")

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

def rebuild_data(engine: DataEngine):
    """Delete all processed data and recompile from cache"""
    print("\nValidating cache before rebuild...")
    is_valid, issues = validate_cache(engine)
    
    if not is_valid:
        print("\nCache validation failed. Issues found:")
        for issue in issues:
            print(f"- {issue}")
            
        print("\nRebuilding with incomplete cache may result in missing data.")
        confirm = input("Continue anyway? (y/N): ")
        if confirm.lower() != 'y':
            print("Operation cancelled.")
            return
    
    # Delete all processed data
    print("\nCleaning up processed data...")
    for path in engine.data_dir.glob("*"):
        if path.is_file():
            print(f"Removing file: {path}")
            path.unlink()
        elif path.is_dir():
            print(f"Removing directory: {path}")
            shutil.rmtree(path)
    
    print("\nRecompiling from cache...")
    engine.cold_start(force_download=False)
    engine.database = CardDatabase()  # Removed data_dir argument
    print("Data rebuild complete!")

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

def handle_cache_maintenance(engine: DataEngine):
    """Handle cache maintenance tasks"""
    print("\nCache Maintenance Options:")
    print("1. Validate Cache Files")
    print("2. Clean Orphaned Files")
    print("3. Rebuild Metadata")
    print("4. Back to Main Menu")
    
    choice = input("\nSelect an option (1-4): ")
    
    if choice == "1":
        # Validate all cache files
        is_valid, issues = validate_cache(engine)
        if is_valid:
            print("\nAll cache files are valid!")
        else:
            print("\nFound issues:")
            for issue in issues:
                print(f"- {issue}")
    
    elif choice == "2":
        # Clean orphaned files
        print("\nChecking for orphaned files...")
        
        # Check set files without metadata
        sets_dir = engine.cache_dir / "scryfall/sets"
        if sets_dir.exists():
            set_files = {f.stem for f in sets_dir.glob("*.json")}
            meta_sets = set(engine.scryfall.metadata['sets'].keys())
            orphaned = set_files - meta_sets
            
            if orphaned:
                print(f"\nFound {len(orphaned)} orphaned set files:")
                for set_code in sorted(orphaned):
                    print(f"- {set_code}")
                
                if input("\nDelete orphaned files? (y/N): ").lower() == 'y':
                    for set_code in orphaned:
                        (sets_dir / f"{set_code}.json").unlink()
                    print("Orphaned files deleted")
            else:
                print("No orphaned set files found")
    
    elif choice == "3":
        # Rebuild metadata
        print("\nRebuilding metadata...")
        engine.scryfall.metadata = {'sets': {}, 'last_update': None}
        
        # Scan all set files
        for set_file in engine.cache_dir.glob("scryfall/sets/*.json"):
            try:
                with open(set_file, 'r') as f:
                    cards = json.load(f)
                if cards:
                    set_code = set_file.stem
                    engine.scryfall.metadata['sets'][set_code] = {
                        'name': cards[0]['set_name'],
                        'card_count': len(cards),
                        'updated_at': datetime.now().isoformat()
                    }
            except Exception as e:
                print(f"Error processing {set_file.name}: {e}")
        
        engine.scryfall.save_metadata()
        print("Metadata rebuilt successfully")
    
    elif choice == "4":
        return
    
    else:
        print("\nInvalid choice")

def view_card_data(engine: DataEngine):
    """Simple card viewer for basic cache validation"""
    print("\nCard Data Viewer")
    print("Enter card name or 'q' to quit")
    
    while True:
        name = input("\nCard name: ").strip()
        if name.lower() == 'q':
            break
            
        # Check if we have the card in cache
        sets_dir = engine.cache_dir / "scryfall/sets"
        found = False
        
        for set_file in sets_dir.glob("*.json"):
            try:
                with open(set_file, 'r', encoding='utf-8') as f:
                    cards = json.load(f)
                    
                for card in cards:
                    if card['name'].lower() == name.lower():
                        found = True
                        print(f"\n=== {card['name']} ===")
                        print(f"Set: {card['set_name']} ({card['set'].upper()})")
                        print(f"Released: {card['released_at']}")
                        print(f"Rarity: {card['rarity']}")
                        if 'oracle_text' in card:
                            print(f"\nText: {card['oracle_text']}")
                        if 'prices' in card and 'usd' in card['prices']:
                            print(f"Price: ${card['prices']['usd']}")
                        print("=" * (len(card['name']) + 8))
                        break
                
                if found:
                    break
                    
            except Exception as e:
                print(f"Error reading {set_file}: {e}")
                continue
        
        if not found:
            print(f"\nCard '{name}' not found in cache")
            print("Note: For full search functionality, use 2.search_cards.py")

def build_sqlite_database(engine: DataEngine):
    """Build SQLite database from cache"""
    print("\nChecking database status...")
    
    # Initialize database
    from src.database.card_database import CardDatabase
    db = CardDatabase()
    
    try:
        if not db.needs_update(engine.cache_dir):
            print("\nDatabase is already up to date!")
            cursor = db.conn.execute("SELECT value FROM version_info WHERE key = 'last_update'")
            last_update = cursor.fetchone()[0]
            print(f"Last updated: {last_update}")
            return
        
        # Load cards from cache
        db.load_from_cache(engine.cache_dir)
        
        # Get count of cards in database
        cursor = db.conn.execute("SELECT COUNT(*) FROM cards")
        count = cursor.fetchone()[0]
        print(f"\nSuccessfully loaded {count} unique cards into database!")
        
    except Exception as e:
        print(f"\nError building database: {e}")
    finally:
        db.close()

def main():
    print_header()
    
    while True:
        choice = show_main_menu()
        
        if choice == "1":  # Show Cache Status
            engine = DataEngine(light_init=True)
            print_cache_status(engine)
            input("\nPress Enter to continue...")
            
        elif choice == "2":  # Fresh Start
            print("\nStarting fresh download of all data...")
            try:
                # Initialize with light_init first to ensure directories are created
                engine = DataEngine(light_init=True)
                
                # Create necessary directories if they don't exist
                (engine.cache_dir / "scryfall/sets").mkdir(parents=True, exist_ok=True)
                (engine.cache_dir / "banlists").mkdir(parents=True, exist_ok=True)
                (engine.cache_dir / "rules").mkdir(parents=True, exist_ok=True)
                (engine.cache_dir / "themes/edhrec").mkdir(parents=True, exist_ok=True)
                
                # Now reinitialize for full operation
                engine = DataEngine()
                
                # Then proceed with downloads
                print("\n1. Downloading card data...")
                if not engine.scryfall.fetch_all_cards(force_download=True):
                    print("Failed to download card data!")
                    input("\nPress Enter to continue...")
                    continue
                
                # Rest of the download operations...
                print("\n2. Downloading banlists...")
                engine.banlist.fetch_banned_cards()
                
                print("\n3. Downloading rules...")
                engine.keywords.download_rules()
                
                print("\n4. Downloading themes...")
                engine.themes.update_all()
                
            except Exception as e:
                print(f"\nError during fresh start: {e}")
                
            input("\nPress Enter to continue...")
            
        elif choice == "3":  # Update Individual Component Cache
            engine = DataEngine()
            while True:
                update_choice = show_update_menu()
                if update_choice == "1":  # Sets
                    engine.scryfall.fetch_all_cards()
                elif update_choice == "2":  # Banlists
                    engine.banlist.fetch_banned_cards()
                elif update_choice == "3":  # Rules
                    engine.keywords.download_rules()
                elif update_choice == "4":  # Themes
                    engine.themes.update_all()
                elif update_choice == "5":  # Everything
                    engine.scryfall.fetch_all_cards()
                    engine.banlist.fetch_banned_cards()
                    engine.keywords.download_rules()
                    engine.themes.update_all()
                elif update_choice == "6":  # Back
                    break
                else:
                    print("\nInvalid choice. Please try again.")
                input("\nPress Enter to continue...")
            
        elif choice == "4":  # Rebuild from Cache
            engine = DataEngine()
            rebuild_data(engine)
            input("\nPress Enter to continue...")
            
        elif choice == "5":  # Cache Maintenance
            engine = DataEngine()
            handle_cache_maintenance(engine)
            input("\nPress Enter to continue...")
            
        elif choice == "6":  # View Card Data
            engine = DataEngine()
            view_card_data(engine)
            input("\nPress Enter to continue...")
            
        elif choice == "7":  # Build SQLite Database
            engine = DataEngine(light_init=True)
            build_sqlite_database(engine)
            input("\nPress Enter to continue...")
            
        elif choice == "8":  # Exit
            print("\nExiting...")
            break
            
        else:
            print("\nInvalid choice. Please try again.")
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    main() 