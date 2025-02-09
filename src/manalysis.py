from typing import Dict
from datetime import datetime
import json
import sqlite3
import pyperclip
import re
from pathlib import Path

class DeckLoader:
    """Handles importing and saving decks"""
    
    def __init__(self, card_db):
        """Initialize loader with card database"""
        self.card_db = card_db
        self.commander = None
        self.data_dir = Path(__file__).parent.parent / "data"
        self.conn = sqlite3.connect(self.data_dir / "decks.db")
        
    def save_deck(self, decklist: Dict[str, int], deck_name: str) -> bool:
        """Save deck to database with proper error handling"""
        try:
            # Create saved_decks directory if it doesn't exist
            saved_dir = self.data_dir / "saved_decks"
            saved_dir.mkdir(parents=True, exist_ok=True)
            
            deck_path = saved_dir / f"{deck_name}.json"
            
            if deck_path.exists():
                print(f"Deck '{deck_name}' already exists!")
                return False
            
            deck_data = {
                "name": deck_name,
                "commander": self.commander,
                "cards": decklist,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            with open(deck_path, 'w') as f:
                json.dump(deck_data, f, indent=2)
            
            # Update database
            with self.conn:
                self.conn.execute("""
                    INSERT INTO decks (name, commander, file_path, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    deck_name,
                    self.commander,
                    str(deck_path),
                    deck_data['created_at'],
                    deck_data['updated_at']
                ))
            
            print(f"Deck '{deck_name}' saved successfully at {deck_path}")
            return True
        
        except sqlite3.IntegrityError:
            print(f"Deck name '{deck_name}' already exists in database!")
            return False
        except Exception as e:
            print(f"Error saving deck: {str(e)}")
            return False

    def load_from_clipboard(self) -> Dict[str, int]:
        """Load deck from clipboard with better validation"""
        try:
            clipboard = pyperclip.paste()
            if not clipboard:
                print("Clipboard is empty!")
                return {}
            
            decklist = {}
            # Improved pattern to handle various formats
            line_pattern = re.compile(r'(\d+)\s*(?:x|\X)?\s*([^#]+)')
            
            for line in clipboard.splitlines():
                line = line.strip()
                if not line:
                    continue
                
                match = line_pattern.match(line)
                if match:
                    quantity = int(match.group(1))
                    raw_name = match.group(2).strip()
                    
                    # Clean up name variations
                    card_name = re.sub(r'\s*[\(\[].*?[\)\]]', '', raw_name)  # Remove set codes
                    card_name = card_name.replace('’', "'")  # Normalize apostrophes
                    
                    # Try multiple lookup strategies
                    card = self.card_db.get_card(card_name)
                    if not card:
                        # Try removing special characters
                        clean_name = re.sub(r"[,'\-]", "", card_name)
                        card = self.card_db.get_card(clean_name)
                    if not card:
                        # Try case-insensitive search
                        card = self.card_db.search_cards(card_name)
                        if card:
                            card = card[0]
                    
                    if not card:
                        print(f"Warning: '{card_name}' not found in database - check spelling or update database")
                        continue
                    
                    decklist[card_name] = quantity
                
            return decklist
        
        except pyperclip.PyperclipException as e:
            print(f"Clipboard access error: {str(e)}")
            return {}
        except Exception as e:
            print(f"Unexpected error loading from clipboard: {str(e)}")
            return {}

    def _parse_deck_text(self, deck_text: str) -> Dict[str, int]:
        # Implementation of _parse_deck_text method
        pass

    def any_card_validation(self, card_name: str) -> bool:
        # Implementation of any_card_validation method
        pass 