from typing import Dict, Optional
import pyperclip
import re
from .models import Card, ManaCost

class DeckLoader:
    """Handles importing decks from clipboard"""
    
    def __init__(self, card_db):
        """
        Initialize loader with card database
        
        Args:
            card_db: Database containing card information and mana values
        """
        self.card_db = card_db
        self.commander = None

    def load_from_clipboard(self) -> Dict[str, int]:
        """
        Load deck from clipboard text
        Format expected:
        1x Lightning Bolt
        4x Mountain
        1 Sewer Nemesis (CLB) 771
        // Sideboard (everything after this is ignored)
        
        Returns:
            Dictionary mapping card names to quantities
        """
        text = pyperclip.paste()
        deck = self._parse_deck_text(text)
        
        if deck:
            # Ask for commander if deck was loaded successfully
            print("\nPlease specify your commander:")
            commander_name = input("> ").strip()
            if commander_name:
                self.commander = commander_name
        
        return deck
    
    def _clean_card_name(self, name: str) -> str:
        """
        Clean up card name by removing set code and collector number
        Examples:
        "Lightning Bolt (CLB) 771" -> "Lightning Bolt"
        "Sewer Nemesis (OTC) 213" -> "Sewer Nemesis"
        """
        # Remove everything after and including the first parenthesis
        return re.sub(r'\s*\(.*$', '', name).strip()
    
    def _parse_deck_text(self, text: str) -> Dict[str, int]:
        """Parse deck text format with 'Nx' quantity format"""
        deck = {}
        
        # Pattern matches: "1x Card Name" or "1 Card Name" with optional set code
        pattern = r'^(\d+)x?\s+(.+)$'
        
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.lower().startswith('//') or line.lower().startswith('sideboard'):
                break
            
            try:
                match = re.match(pattern, line)
                if match:
                    quantity = int(match.group(1))
                    card_name = self._clean_card_name(match.group(2))
                    if quantity > 0:
                        deck[card_name] = quantity
                else:
                    print(f"Warning: Couldn't parse line: {line}")
            except (ValueError, IndexError):
                print(f"Warning: Couldn't parse line: {line}")
                continue
        
        return deck 