# Move from src/run_engine.py to /run_engine.py 
from src.collectors.data_engine import DataEngine
from src.database.card_database import CardDatabase
from pathlib import Path
import shutil
import json
from datetime import datetime

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
    print("7. Exit")
    return input("\nSelect an option (1-7): ")

def show_update_menu():
    print("\nUpdate Component Cache:")
    print("1. Download New Sets")
    print("2. Update Rules")
    print("3. Update Themes")
    print("4. Rebuild Name Index")
    print("5. Update Everything")
    print("6. Back to Main Menu")
    return input("\nSelect an option (1-6): ")

def show_cache_menu():
    print("\nCache Maintenance:")
    print("1. Show Cache Size")
    print("2. Clean Old Cache Files")
    print("3. Verify Cache Integrity")
    print("4. Delete All Cache")
    print("5. Back to Main Menu")
    return input("\nSelect an option (1-5): ")

def validate_cache(engine: DataEngine) -> tuple[bool, list[str]]:
    """Validate all cache files"""
    issues = []
    
    # Check Scryfall cache
    print("\nChecking Scryfall cache:")
    bulk_cache = engine.cache_dir / "scryfall/bulk_cards_cache.json"
    if not bulk_cache.exists():
        issues.append("Missing Scryfall bulk cache")
    else:
        print(f"- Found {bulk_cache}")
    
    # Check themes cache
    print("\nChecking optional themes_raw.json:")
    themes_cache = engine.cache_dir / "themes/edhrec/themes_raw.json"
    if not themes_cache.exists():
        print(f"- Note: Recommended cache file missing: {themes_cache}")
    else:
        print(f"- Found {themes_cache}")
    
    # Check rules cache
    print("\nChecking optional MagicCompRules.txt:")
    rules_cache = engine.cache_dir / "rules/MagicCompRules.txt"
    if not rules_cache.exists():
        print(f"- Note: Recommended cache file missing: {rules_cache}")
    else:
        print(f"- Found {rules_cache}")
    
    return len(issues) == 0, issues

def print_cache_status(engine: DataEngine):
    """Display current cache status"""
    is_valid, issues = validate_cache(engine)
    if is_valid:
        print("Cache validation successful!")
    else:
        print("\nCache validation failed. Issues found:")
        for issue in issues:
            print(f"- {issue}")

def get_cache_size(path: Path) -> tuple[int, dict]:
    """Get total size and breakdown of cache directory"""
    total_size = 0
    breakdown = {}
    
    for item in path.rglob('*'):
        if item.is_file():
            size = item.stat().st_size
            total_size += size
            category = item.parent.name
            breakdown[category] = breakdown.get(category, 0) + size
            
    return total_size, breakdown

def clean_old_cache(engine: DataEngine, days: int):
    """Remove cache files older than specified days"""
    cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
    cleaned = 0
    size_freed = 0
    
    for path in engine.cache_dir.rglob('*'):
        if path.is_file():
            mtime = path.stat().st_mtime
            if mtime < cutoff:
                size = path.stat().st_size
                print(f"Removing {path}")
                path.unlink()
                cleaned += 1
                size_freed += size
    
    if cleaned:
        print(f"\nCleaned {cleaned} files")
        print(f"Freed {size_freed/1024/1024:.1f}MB of space")
    else:
        print("\nNo files needed cleaning")

def handle_cache_maintenance(engine: DataEngine):
    """Handle cache maintenance menu"""
    while True:
        choice = show_cache_menu()
        
        if choice == '1':
            total, breakdown = get_cache_size(engine.cache_dir)
            print("\nCache Size Breakdown:")
            for category, size in breakdown.items():
                print(f"- {category}: {size/1024/1024:.1f} MB")
            print(f"\nTotal Cache Size: {total/1024/1024:.1f} MB")
            
        elif choice == '2':
            days = int(input("\nClean files older than how many days? (default: 30) ") or "30")
            clean_old_cache(engine, days)
            
        elif choice == '3':
            print("\nVerifying cache integrity...")
            is_valid, issues = validate_cache(engine)
            if is_valid:
                print("All cache files are valid!")
            else:
                print("\nIssues found:")
                for issue in issues:
                    print(f"- {issue}")
                    
        elif choice == '4':
            print("\nWARNING: This will delete all cached data!")
            print("You will need to download everything again.")
            if input("Are you sure? (yes/N): ").lower() == 'yes':
                shutil.rmtree(engine.cache_dir)
                engine.cache_dir.mkdir(parents=True)
                print("Cache deleted successfully")
            else:
                print("Operation cancelled")
                
        elif choice == '5':
            break
            
        else:
            print("\nInvalid choice. Please try again.")
        
        input("\nPress Enter to continue...")

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
    else:
        print("Cache validation successful!")
        confirm = input("\nThis will delete all processed data and recompile from cache. Continue? (y/N): ")
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
    
    # Load cached card data
    print("\n1. Loading cached card data...")
    with open(engine.cache_dir / "scryfall/bulk_cards_cache.json", 'r', encoding='utf-8') as f:
        cards = json.load(f)
    
    print("\n2. Processing card data...")
    engine.database = CardDatabase(data_dir=str(engine.data_dir / "database"))
    engine.database.update_from_scryfall(cards)
    
    print("\n3. Building name index...")
    engine.database.build_name_index()
    
    print("\n4. Processing additional components...")
    engine.cold_start(force_download=False)
    
    print("Data rebuild complete!")

def view_card_data(engine: DataEngine):
    name = input("\nEnter card name: ").lower()
    card_data = engine.database.name_index.get(name)
    
    if card_data:
        print(f"\nCard: {card_data['name']}")
        
        print("\nOracle Text History:")
        for oracle_text, version in card_data['oracle_versions'].items():
            print(f"\nVersion from {version['first_printed']}:")
            print(f"Mana Cost: {version['mana_cost']}")
            print(f"Type Line: {version['type_line']}")
            print(f"Oracle Text: {version['oracle_text']}")
            print(f"Color Identity: {', '.join(version['color_identity']) if version['color_identity'] else 'Colorless'}")
            print(f"Sets: {', '.join(version['sets'])}")
        
        print("\nAll Printings (chronological order):")
        for printing in card_data['printings']:
            price = printing['prices'].get('usd', 'N/A')
            print(f"- {printing['set_name']} ({printing['set']}) - {printing['rarity']} - ${price}")
        
        print(f"\nTotal printings: {len(card_data['printings'])}")
        
        print("\nCurrent Legalities:")
        latest_version = list(card_data['oracle_versions'].values())[-1]
        for format_name, status in sorted(latest_version['legalities'].items()):
            if status != 'not_legal':
                print(f"- {format_name}: {status}")
    else:
        print(f"\nCard '{name}' not found.")

def main():
    print_header()
    
    while True:
        choice = show_main_menu()
        
        if choice == "1":  # Show Cache Status
            engine = DataEngine(light_init=True)
            print_cache_status(engine)
            input("\nPress Enter to continue...")
            
        elif choice == "2":  # Fresh Start
            print("\nStarting fresh download and compilation of all data...")
            engine = DataEngine()
            engine.cold_start(force_download=True)
            input("\nPress Enter to continue...")
            
        elif choice == "3":  # Update Individual Component Cache
            engine = DataEngine()
            if not engine._has_card_cache():
                print("\nCache is empty! Please use option 2 (Fresh Start) to download data first.")
                input("\nPress Enter to continue...")
                continue
                
            while True:
                update_choice = show_update_menu()
                if update_choice == "1":
                    engine.update_if_needed('sets')
                    input("\nPress Enter to continue...")
                elif update_choice == "2":
                    engine.update_if_needed('rules')
                    input("\nPress Enter to continue...")
                elif update_choice == "3":
                    engine.update_if_needed('themes')
                    input("\nPress Enter to continue...")
                elif update_choice == "4":
                    print("\nRebuilding name index...")
                    engine.database.build_name_index()
                    input("\nPress Enter to continue...")
                elif update_choice == "5":
                    engine.update_if_needed()  # Updates everything
                    input("\nPress Enter to continue...")
                elif update_choice == "6":  # Back to Main Menu
                    break
                else:
                    print("\nInvalid choice. Please try again.")
                    input("\nPress Enter to continue...")
            
        elif choice == "4":  # Rebuild from Cache
            engine = DataEngine()
            if not engine._has_card_cache():
                print("\nCache is empty! Please use option 2 (Fresh Start) to download data first.")
                input("\nPress Enter to continue...")
                continue
            rebuild_data(engine)
            input("\nPress Enter to continue...")
            
        elif choice == "5":  # Cache Maintenance
            engine = DataEngine()
            handle_cache_maintenance(engine)
            input("\nPress Enter to continue...")
            
        elif choice == "6":  # View Card Data
            engine = DataEngine()
            if not engine.database or not engine.database.cards:
                print("\nNo card data available. Please use option 2 (Fresh Start) first.")
                input("\nPress Enter to continue...")
                continue
            view_card_data(engine)
            input("\nPress Enter to continue...")
            
        elif choice == "7":  # Exit
            print("\nExiting...")
            break
            
        else:
            print("\nInvalid choice. Please try again.")
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    main() 