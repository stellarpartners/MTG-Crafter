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
    
    for name, path in cache_files.items():
        print(f"\nChecking {name}:")
        print(f"Path: {path}")
        if path.exists():
            size = path.stat().st_size
            modified = path.stat().st_mtime
            print(f"- Status: Present")
            print(f"- Size: {format_size(size)}")
            print(f"- Modified: {format_date(modified)}")
        else:
            print(f"- Status: Missing")
    
    # Theme cache
    print("\nTheme Cache:")
    theme_cache = engine.cache_dir / "themes/edhrec/themes_raw.json"
    print(f"Path: {theme_cache}")
    if theme_cache.exists():
        size = theme_cache.stat().st_size
        modified = theme_cache.stat().st_mtime
        print(f"- Status: Present")
        print(f"- Size: {format_size(size)}")
        print(f"- Modified: {format_date(modified)}")
    else:
        print(f"- Status: Missing")
    
    # Rules cache
    print("\nRules Cache:")
    rules_cache = engine.cache_dir / "rules/MagicCompRules.txt"
    print(f"Path: {rules_cache}")
    if rules_cache.exists():
        size = rules_cache.stat().st_size
        modified = rules_cache.stat().st_mtime
        print(f"- Status: Present")
        print(f"- Size: {format_size(size)}")
        print(f"- Modified: {format_date(modified)}")
    else:
        print(f"- Status: Missing")

def show_main_menu():
    print("\nMain Menu:")
    print("1. Show Cache Status")
    print("2. Fresh Start (Download & Compile Everything)")
    print("3. Compile Data from Cache")
    print("4. Update Components")
    print("5. Rebuild Data (Recompile from Cache)")
    print("6. Cache Maintenance")
    print("7. Exit")
    return input("\nSelect an option (1-7): ")

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
    data_dirs = [
        Path("data/database"),
        Path("data/themes"),
        Path("data/metadata.json")
    ]
    
    print("\nCleaning up processed data...")
    for path in data_dirs:
        if path.is_file() and path.exists():
            print(f"Removing file: {path}")
            path.unlink()
        elif path.is_dir() and path.exists():
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
    engine = DataEngine()
    
    while True:
        choice = show_main_menu()
        
        if choice == '1':
            print_cache_status(engine)
            
        elif choice == '2':
            print("\nStarting fresh download and compilation...")
            engine.cold_start(force_download=True)
            
        elif choice == '3':
            print("\nCompiling from cached data...")
            engine.cold_start(force_download=False)
            
        elif choice == '4':
            while True:
                update_choice = show_update_menu()
                
                if update_choice == '1':
                    print("\nUpdating card data...")
                    engine.update_if_needed('cards')
                elif update_choice == '2':
                    print("\nUpdating rules...")
                    engine.update_if_needed('rules')
                elif update_choice == '3':
                    print("\nUpdating themes...")
                    engine.update_if_needed('themes')
                elif update_choice == '4':
                    print("\nUpdating all components...")
                    engine.update_if_needed()
                elif update_choice == '5':
                    break
                else:
                    print("\nInvalid choice. Please try again.")
                
                input("\nPress Enter to continue...")
                
        elif choice == '5':
            rebuild_data(engine)
            
        elif choice == '6':
            handle_cache_maintenance(engine)
            
        elif choice == '7':
            print("\nExiting MTG Crafter Engine...")
            sys.exit(0)
            
        else:
            print("\nInvalid choice. Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main() 