"""
DeckLoader class for managing Magic: The Gathering deck loading and saving
"""

from pathlib import Path
from typing import Dict, List
import json
from datetime import datetime
import re

class DeckLoader:
    """Class for loading and saving Magic: The Gathering decklists"""
    
    def __init__(self, card_db):
        """Initialize the deck loader with card database"""
        self.card_db = card_db
        self.commander = None
    
    def load_from_clipboard(self) -> Dict[str, int]:
        """Load decklist from clipboard"""
        try:
            import pyperclip
            text = pyperclip.paste()
        except ImportError:
            raise ImportError("pyperclip package required for clipboard support")
        
        if not text:
            return {}
        
        decklist = {}
        commander_pattern = re.compile(r'(?:COMMANDER|CMDR):\s*(.+)')
        card_pattern = re.compile(r'(\d+)x?\s+(.+)')
        
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Check for commander
            cmdr_match = commander_pattern.match(line)
            if cmdr_match:
                self.commander = cmdr_match.group(1).strip()
                continue
            
            # Parse card entries
            card_match = card_pattern.match(line)
            if card_match:
                quantity = int(card_match.group(1))
                card_name = card_match.group(2).strip()
                
                # Validate card exists in database
                if self.card_db.get_card(card_name):
                    decklist[card_name] = quantity
                else:
                    print(f"Warning: Card not found in database: {card_name}")
        
        return decklist
    
    def list_saved_decks(self) -> List[Dict]:
        """List all saved decks with their metadata"""
        decks = []
        save_dir = Path("saved_decks")
        
        if not save_dir.exists():
            save_dir.mkdir(exist_ok=True)
            return decks
        
        for deck_file in save_dir.glob("*.json"):
            try:
                with open(deck_file, 'r') as f:
                    deck_data = json.load(f)
                    decks.append({
                        'name': deck_data.get('name', deck_file.stem),
                        'commander': deck_data.get('commander', 'Unknown'),
                        'total_cards': sum(deck_data.get('cards', {}).values()),
                        'manalysis': deck_data.get('manalysis', None)
                    })
            except Exception as e:
                print(f"Warning: Could not load {deck_file}: {str(e)}")
                continue
        
        return decks
    
    def save_deck(self, decklist: Dict[str, int], name: str) -> bool:
        """Save a deck with its metadata"""
        save_dir = Path("saved_decks")
        save_dir.mkdir(exist_ok=True)
        
        deck_data = {
            'name': name,
            'commander': self.commander,
            'cards': decklist,
            'created_at': datetime.now().isoformat()
        }
        
        try:
            with open(save_dir / f"{name}.json", 'w') as f:
                json.dump(deck_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving deck: {str(e)}")
            return False
    
    def load_saved_deck_with_data(self, deck_identifier: str) -> Dict:
        """Load a saved deck with all its data"""
        save_dir = Path("saved_decks")
        
        # Handle numeric input
        if deck_identifier.isdigit():
            decks = self.list_saved_decks()
            idx = int(deck_identifier) - 1
            if 0 <= idx < len(decks):
                deck_identifier = decks[idx]['name']
        
        deck_path = save_dir / f"{deck_identifier}.json"
        if not deck_path.exists():
            # Try case-insensitive search
            for file in save_dir.glob("*.json"):
                if file.stem.lower() == deck_identifier.lower():
                    deck_path = file
                    break
            if not deck_path.exists():
                raise ValueError(f"Deck '{deck_identifier}' not found")
        
        try:
            with open(deck_path, 'r') as f:
                deck_data = json.load(f)
                self.commander = deck_data.get('commander')
                return deck_data
        except Exception as e:
            raise ValueError(f"Error loading deck: {str(e)}")
    
    def update_deck(self, deck_identifier: str, new_decklist: Dict[str, int]) -> bool:
        """Update an existing deck with new card list"""
        save_dir = Path("saved_decks")
        
        # Handle numeric input
        if deck_identifier.isdigit():
            decks = self.list_saved_decks()
            idx = int(deck_identifier) - 1
            if 0 <= idx < len(decks):
                deck_identifier = decks[idx]['name']
        
        deck_path = save_dir / f"{deck_identifier}.json"
        if not deck_path.exists():
            # Try case-insensitive search
            for file in save_dir.glob("*.json"):
                if file.stem.lower() == deck_identifier.lower():
                    deck_path = file
                    break
            if not deck_path.exists():
                return False
        
        try:
            with open(deck_path, 'r') as f:
                deck_data = json.load(f)
            
            deck_data['cards'] = new_decklist
            deck_data['updated_at'] = datetime.now().isoformat()
            # Remove old analysis when deck is updated
            deck_data.pop('manalysis', None)
            
            with open(deck_path, 'w') as f:
                json.dump(deck_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error updating deck: {str(e)}")
            return False
    
    def save_manalysis(self, deck_identifier: str, analysis_results: Dict) -> bool:
        """Save analysis results for a deck"""
        save_dir = Path("saved_decks")
        
        # Handle numeric input
        if deck_identifier.isdigit():
            decks = self.list_saved_decks()
            idx = int(deck_identifier) - 1
            if 0 <= idx < len(decks):
                deck_identifier = decks[idx]['name']
        
        deck_path = save_dir / f"{deck_identifier}.json"
        if not deck_path.exists():
            # Try case-insensitive search
            for file in save_dir.glob("*.json"):
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