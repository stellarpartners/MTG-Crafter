from typing import Dict, List, Optional
import pyperclip
import re
from pathlib import Path
import json
from datetime import datetime
from src.database.card_database import CardDatabase
from .models import Card, ManaCost
from src.database.card_repository import CardRepository

class DeckLoader:
    """Handles importing and saving decks"""
    
    def __init__(self, card_repo: CardRepository):
        """
        Initialize deck loader with card repository
        
        Args:
            card_repo: CardRepository object for card validation
        """
        self.card_repo = card_repo
        self.deck_dir = Path("saved_decks")
        self.deck_dir.mkdir(exist_ok=True)
        self.commander = None

    def load_from_clipboard(self) -> Dict[str, int]:
        """Load deck from clipboard text"""
        try:
            text = pyperclip.paste()
        except ImportError:
            raise ImportError("pyperclip package required for clipboard support")
            
        if not text:
            return {}
            
        deck = self._parse_deck_text(text)
        
        # Check for commander in text first
        commander_pattern = re.compile(r'(?:COMMANDER|CMDR):\s*(.+)')
        for line in text.splitlines():
            cmdr_match = commander_pattern.match(line.strip())
            if cmdr_match:
                self.commander = cmdr_match.group(1).strip()
                break
        
        # If no commander found in text, ask user
        if not self.commander and deck:
            print("\nWould you like to specify a commander? (1=yes, 0=no):")
            choice = input("> ").strip()
            if choice == '1':
                commander_name = input("Enter commander name: ").strip()
                if commander_name:
                    self.commander = commander_name
        
        return deck
    
    def _clean_card_name(self, name: str) -> str:
        """Clean up card name by removing set code and collector number"""
        return re.sub(r'\s*\(.*$', '', name).strip()
    
    def _parse_deck_text(self, text: str) -> Dict[str, int]:
        """Parse deck text format"""
        deck = {}
        pattern = r'^(\d+)x?\s+(.+)$'
        
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            
            # Stop parsing when we hit sideboard
            if line.lower().startswith(('sideboard', 'sb:', 'sb ')):
                break
            
            # Skip comment lines and commander line
            if line.lower().startswith(('/', 'commander:', 'cmdr:')):
                continue
            
            try:
                match = re.match(pattern, line)
                if match:
                    quantity = int(match.group(1))
                    card_name = self._clean_card_name(match.group(2))
                    
                    # Validate card exists in database
                    if self.card_repo.get_card(card_name):
                        deck[card_name] = quantity
                    else:
                        print(f"Warning: Card not found: {card_name}")
            except (ValueError, IndexError):
                print(f"Warning: Couldn't parse line: {line}")
                continue
        
        return deck
    
    def _sanitize_filename(self, name: str) -> str:
        """Convert deck name to a valid filename"""
        # Replace spaces and special characters with underscores
        return re.sub(r'[^\w-]', '_', name)
    
    def save_deck(self, decklist: Dict[str, int], name: str) -> bool:
        """Save a deck with its metadata"""
        try:
            print("\nDebug: Starting deck save...")
            
            if not decklist:
                print("Error: Cannot save empty deck")
                return False
            
            if not name:
                print("Error: Deck name cannot be empty")
                return False
            
            print(f"Debug: Saving deck '{name}' with {len(decklist)} cards")
            
            # Use the consistent deck directory
            print(f"Debug: Save directory is {self.deck_dir.absolute()}")
            
            # Prepare the file path with sanitized filename
            safe_filename = self._sanitize_filename(name)
            file_path = self.deck_dir / f"{safe_filename}.json"
            print(f"Debug: Will save to {file_path}")
            
            # Check if file already exists
            if file_path.exists():
                print(f"Warning: Deck '{name}' already exists")
                overwrite = input("Would you like to overwrite it? (1=yes, 0=no): ").strip()
                if overwrite != '1':
                    return False
            
            # Prepare deck data (store original name)
            deck_data = {
                'name': name,  # Store original name
                'filename': safe_filename,  # Store sanitized filename
                'commander': self.commander,
                'cards': decklist,
                'created_at': datetime.now().isoformat()
            }
            print(f"Debug: Deck data prepared. Commander: {self.commander}, Cards: {len(decklist)}")
            
            # Save the file
            print("Debug: Attempting to save file...")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(deck_data, f, indent=2, ensure_ascii=False)
            print("Debug: File written")
            
            # Verify the file was created
            if not file_path.exists():
                print("Error: Failed to create deck file")
                return False
            
            # Verify the file contains the correct data
            print("Debug: Verifying saved data...")
            with open(file_path, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
                if saved_data.get('cards') != decklist:
                    print("Error: Deck data verification failed")
                    print(f"Debug: Original cards: {len(decklist)}")
                    print(f"Debug: Saved cards: {len(saved_data.get('cards', {}))}")
                    return False
            
            print("Debug: Deck saved successfully!")
            return True
        
        except Exception as e:
            print(f"Error saving deck: {str(e)}")
            print(f"Debug: Exception type: {type(e)}")
            import traceback
            print(f"Debug: Traceback:\n{traceback.format_exc()}")
            return False
    
    def list_saved_decks(self) -> List[Dict]:
        """List all saved decks with metadata"""
        decks = []
        for deck_file in self.deck_dir.glob("*.json"):
            try:
                with open(deck_file, 'r') as f:
                    data = json.load(f)
                    decks.append({
                        'id': deck_file.stem,
                        'name': data.get('name', deck_file.stem),
                        'commander': data.get('commander', 'Unknown')
                    })
            except Exception as e:
                print(f"Error reading {deck_file}: {str(e)}")
        return decks
    
    def load_saved_deck_with_data(self, deck_identifier: str) -> Dict:
        """Load a saved deck with all its data"""
        # Handle numeric input
        if deck_identifier.isdigit():
            decks = self.list_saved_decks()
            idx = int(deck_identifier) - 1
            if 0 <= idx < len(decks):
                deck_identifier = decks[idx]['name']  # Use the deck's name, not the index
            else:
                raise ValueError(f"Invalid deck number: {deck_identifier}")
        
        deck_path = self.deck_dir / f"{self._sanitize_filename(deck_identifier)}.json"
        if not deck_path.exists():
            # Try case-insensitive search
            for file in self.deck_dir.glob("*.json"):
                if file.stem.lower() == self._sanitize_filename(deck_identifier).lower():
                    deck_path = file
                    break
            if not deck_path.exists():
                raise ValueError(f"Deck '{deck_identifier}' not found")
        
        try:
            with open(deck_path, 'r', encoding='utf-8') as f:
                deck_data = json.load(f)
                self.commander = deck_data.get('commander')
                return deck_data
        except Exception as e:
            raise ValueError(f"Error loading deck: {str(e)}")
    
    def update_deck(self, deck_identifier: str) -> bool:
        """Update an existing deck with new information"""
        try:
            # Handle numeric input
            if deck_identifier.isdigit():
                decks = self.list_saved_decks()
                idx = int(deck_identifier) - 1
                if 0 <= idx < len(decks):
                    deck_identifier = decks[idx]['name']  # Use the deck's name
                else:
                    print(f"Error: Invalid deck number: {deck_identifier}")
                    return False
            
            deck_path = self.deck_dir / f"{self._sanitize_filename(deck_identifier)}.json"
            if not deck_path.exists():
                # Try case-insensitive search
                for file in self.deck_dir.glob("*.json"):
                    if file.stem.lower() == self._sanitize_filename(deck_identifier).lower():
                        deck_path = file
                        break
                if not deck_path.exists():
                    print(f"Error: Deck '{deck_identifier}' not found")
                    return False
            
            with open(deck_path, 'r') as f:
                deck_data = json.load(f)
            
            print("\nWhat would you like to update?")
            print("1. Deck Name")
            print("2. Commander")
            print("3. Cards (from clipboard)")
            
            choice = input("\nEnter your choice (1-3): ").strip()
            
            if choice == "1":
                new_name = input("Enter new deck name: ").strip()
                if new_name:
                    # Create new file with new name
                    new_path = self.deck_dir / f"{new_name}.json"
                    deck_data['name'] = new_name
                    with open(new_path, 'w') as f:
                        json.dump(deck_data, f, indent=2)
                    # Remove old file
                    deck_path.unlink()
                    print(f"Deck renamed to '{new_name}'")
                    return True
            
            elif choice == "2":
                new_commander = input("Enter new commander: ").strip()
                if new_commander:
                    deck_data['commander'] = new_commander
                    print(f"Commander updated to '{new_commander}'")
            
            elif choice == "3":
                print("Reading new decklist from clipboard...")
                new_decklist = self._parse_deck_text(pyperclip.paste())
                if new_decklist:
                    deck_data['cards'] = new_decklist
                    print(f"Updated deck with {sum(new_decklist.values())} cards")
                    # Remove old analysis when cards are updated
                    deck_data.pop('manalysis', None)
                else:
                    print("Error: No valid decklist found in clipboard")
                    return False
            else:
                print("Invalid choice")
                return False
            
            # Save updates
            deck_data['updated_at'] = datetime.now().isoformat()
            with open(deck_path, 'w') as f:
                json.dump(deck_data, f, indent=2)
            return True
        
        except Exception as e:
            print(f"Error updating deck: {str(e)}")
            return False
    
    def save_manalysis(self, deck_identifier: str, analysis_results: Dict) -> bool:
        """Save analysis results for a deck"""
        deck_path = self.deck_dir / f"{deck_identifier}.json"
        if not deck_path.exists():
            # Try case-insensitive search
            for file in self.deck_dir.glob("*.json"):
                if file.stem.lower() == deck_identifier.lower():
                    deck_path = file
                    break
            if not deck_path.exists():
                return False
        
        try:
            with open(deck_path, 'r') as f:
                deck_data = json.load(f)
            
            deck_data['manalysis'] = analysis_results
            deck_data['analyzed_at'] = datetime.now().isoformat()
            
            with open(deck_path, 'w') as f:
                json.dump(deck_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving analysis: {str(e)}")
            return False

    def load_deck(self, deck_id: str) -> Dict[str, int]:
        """Load a saved deck by ID (filename)"""
        deck_path = self.deck_dir / f"{deck_id}.json"
        if not deck_path.exists():
            return {}
            
        with open(deck_path, 'r') as f:
            raw_deck = json.load(f)
            
        return {
            name: qty 
            for name, qty in raw_deck.items() 
            if self.card_repo.get_card(name)  # Repository validation
        } 