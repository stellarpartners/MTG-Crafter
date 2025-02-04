from collectors.data_engine import DataEngine
from datetime import datetime
from pathlib import Path
import sys
import json
import shutil

def print_header():
    print("\nMTG Crafter Engine")
    print("=================")

def print_cache_status(engine: DataEngine):
    """Print status of cached data"""
    def format_size(size_bytes):
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} GB"
    
    def format_date(timestamp):
        """Format timestamp in readable format"""
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M")
    
    print("\nCache Status:")
    
    # Scryfall cache
    print("\nScryfall Cache:")
    cache_files = {
        'Bulk Data': engine.cache_dir / "scryfall/bulk_cards_cache.json",
        'Metadata': engine.cache_dir / "scryfall/bulk_cache_metadata.json"
    }
    
    has_valid_cache = True
    for name, path in cache_files.items():
        print(f"\nChecking {name}:")
        print(f"Path: {path}")
        if path.exists():
            try:
                # Try to validate JSON
                with open(path, 'r', encoding='utf-8') as f:
                    json.load(f)
                size = path.stat().st_size
                modified = path.stat().st_mtime
                print(f"- Status: Valid")
                print(f"- Size: {format_size(size)}")
                print(f"- Modified: {format_date(modified)}")
            except json.JSONDecodeError:
                print(f"- Status: Corrupted (Invalid JSON)")
                has_valid_cache = False
            except Exception as e:
                print(f"- Status: Error ({str(e)})")
                has_valid_cache = False
        else:
            print(f"- Status: Missing")
            has_valid_cache = False
    
    if not has_valid_cache:
        print("\n⚠️ Cache appears to be corrupted or incomplete!")
        print("Recommendation: Use option 2 (Fresh Start) to rebuild the cache.")
        return
    
    # Theme cache
    print("\nTheme Cache:")
    theme_cache = engine.cache_dir / "themes/edhrec/themes_raw.json"
    print(f"Path: {theme_cache}")
    if theme_cache.exists():
        try:
            with open(theme_cache, 'r', encoding='utf-8') as f:
                json.load(f)
            size = theme_cache.stat().st_size
            modified = theme_cache.stat().st_mtime
            print(f"- Status: Valid")
            print(f"- Size: {format_size(size)}")
            print(f"- Modified: {format_date(modified)}")
        except json.JSONDecodeError:
            print(f"- Status: Corrupted (Invalid JSON)")
        except Exception as e:
            print(f"- Status: Error ({str(e)})")
    else:
        print(f"- Status: Missing")
    
    # Rules cache
    print("\nRules Cache:")
    rules_cache = engine.cache_dir / "rules/MagicCompRules.txt"
    print(f"Path: {rules_cache}")
    if rules_cache.exists():
        try:
            size = rules_cache.stat().st_size
            modified = rules_cache.stat().st_mtime
            print(f"- Status: Present")
            print(f"- Size: {format_size(size)}")
            print(f"- Modified: {format_date(modified)}")
        except Exception as e:
            print(f"- Status: Error ({str(e)})")
    else:
        print(f"- Status: Missing")

def show_main_menu():
    print("\nMain Menu:")
    print("1. Show Cache Status")
    print("2. Fresh Start (Download & Compile Everything)")
    print("3. Update Individual Component Cache")
    print("4. Rebuild from Cache (Delete processed data & recompile)")
    print("5. Cache Maintenance")
    print("6. Exit")
    return input("\nSelect an option (1-6): ")

def show_update_menu():
    print("\nUpdate Menu:")
    print("1. Update Card Data")
    print("2. Update Rules")
    print("3. Update Themes")
    print("4. Update Everything")
    print("5. Back to Main Menu")
    return input("\nSelect an option (1-5): ")

def show_cache_menu():
    print("\nCache Maintenance:")
    print("1. Show Cache Size")
    print("2. Clean Old Cache Files")
    print("3. Verify Cache Integrity")
    print("4. Delete All Cache")
    print("5. Back to Main Menu")
    return input("\nSelect an option (1-5): ")

def validate_cache(engine: DataEngine) -> tuple[bool, list[str]]:
    """
    Validate that all required cache files exist and are valid
    Returns: (is_valid, list of issues)
    """
    issues = []
    
    # Required cache files and their minimum sizes
    required_files = {
        engine.cache_dir / "scryfall/bulk_cards_cache.json": 1_000_000,    # At least 1MB
        engine.cache_dir / "scryfall/bulk_cache_metadata.json": 100,       # At least 100B
    }
    
    # Optional but recommended files
    optional_files = {
        engine.cache_dir / "themes/edhrec/themes_raw.json": 1_000,   # At least 1KB
        engine.cache_dir / "rules/MagicCompRules.txt": 100_000,      # At least 100KB
    }
    
    print("\nChecking cache files...")
    
    # Check required files
    for path, min_size in required_files.items():
        print(f"\nChecking {path.name}:")
        if not path.exists():
            msg = f"Missing required cache file: {path}"
            print(f"- Error: {msg}")
            issues.append(msg)
            continue
            
        try:
            # Check file size
            size = path.stat().st_size
            if size < min_size:
                msg = f"Cache file too small ({size} bytes): {path}"
                print(f"- Warning: {msg}")
                issues.append(msg)
            else:
                print(f"- Size OK: {size} bytes")
                
            # Validate JSON format for json files
            if path.suffix == '.json':
                try:
                    with open(path, 'r') as f:
                        json.load(f)
                    print("- JSON format OK")
                except json.JSONDecodeError as e:
                    msg = f"Invalid JSON in cache file: {path} - {str(e)}"
                    print(f"- Error: {msg}")
                    issues.append(msg)
                    
        except Exception as e:
            msg = f"Error checking cache file {path}: {e}"
            print(f"- Error: {msg}")
            issues.append(msg)
    
    # Check optional files
    for path, min_size in optional_files.items():
        print(f"\nChecking optional {path.name}:")
        if not path.exists():
            print(f"- Note: Recommended cache file missing: {path}")
            continue
            
        size = path.stat().st_size
        if size < min_size:
            print(f"- Warning: File might be incomplete ({size} bytes)")
        else:
            print(f"- Size OK: {size} bytes")
    
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
    engine.cold_start(force_download=False)
    print("Data rebuild complete!")

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

def clean_old_cache(engine: DataEngine, days: int = 30):
    """Clean cache files older than specified days"""
    print(f"\nLooking for cache files older than {days} days...")
    now = datetime.now().timestamp()
    cleaned = 0
    saved_space = 0
    
    for path in engine.cache_dir.rglob('*'):
        if path.is_file():
            age = (now - path.stat().st_mtime) / (24 * 3600)  # Convert to days
            if age > days:
                size = path.stat().st_size
                print(f"Found old file: {path.relative_to(engine.cache_dir)}")
                print(f"- Age: {age:.1f} days")
                print(f"- Size: {size/1024/1024:.1f} MB")
                if input("Delete this file? (y/N): ").lower() == 'y':
                    path.unlink()
                    cleaned += 1
                    saved_space += size
    
    if cleaned:
        print(f"\nCleaned {cleaned} files")
        print(f"Saved {saved_space/1024/1024:.1f} MB")
    else:
        print("\nNo old cache files found")

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
                    engine.update_if_needed()  # Updates everything
                    input("\nPress Enter to continue...")
                elif update_choice == "5":  # Back to Main Menu
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
            
        elif choice == "6":  # Exit
            print("\nExiting...")
            break
            
        else:
            print("\nInvalid choice. Please try again.")
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    main() 