import json
from pathlib import Path

def sort_json_file(file_path: Path):
    """Sort a JSON file alphabetically by keys"""
    print(f"Sorting {file_path}...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, dict):
            # Sort dictionary by keys
            sorted_data = dict(sorted(data.items()))
            # Also sort nested dictionaries
            for key, value in sorted_data.items():
                if isinstance(value, dict):
                    sorted_data[key] = dict(sorted(value.items()))
        elif isinstance(data, list):
            # Check if it's a list of dictionaries
            if data and isinstance(data[0], dict):
                # For card data files
                if 'cards_' in file_path.name:
                    print(f"Detected card file: {file_path.name}")
                    # Keep original order for card files
                    sorted_data = data
                else:
                    # For other list of dictionaries, try to sort by name
                    try:
                        sorted_data = sorted(data, key=lambda x: str(x))
                    except TypeError:
                        print(f"Could not sort list in {file_path.name}, keeping original order")
                        sorted_data = data
            else:
                # Sort simple lists
                sorted_data = sorted(data)
        else:
            print(f"Skipping {file_path.name} - not a dictionary or list")
            return
        
        # Save sorted data
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(sorted_data, f, indent=2)
        
        print(f"Successfully sorted {file_path}")
        
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")

def sort_all_json_files():
    """Sort all JSON files in data directory"""
    # Sort processed files
    processed_dir = Path("data/processed")
    if processed_dir.exists():
        print("\nProcessing files in data/processed/")
        for json_file in processed_dir.glob("*.json"):
            sort_json_file(json_file)
    
    # Sort raw files
    raw_dir = Path("data/raw")
    if raw_dir.exists():
        print("\nProcessing files in data/raw/")
        for json_file in raw_dir.glob("*.json"):
            if 'cards_' not in json_file.name:  # Skip card files
                sort_json_file(json_file)
            else:
                print(f"Skipping card file: {json_file.name}")

if __name__ == "__main__":
    print("Starting JSON file sorting...")
    sort_all_json_files()
    print("\nDone!") 