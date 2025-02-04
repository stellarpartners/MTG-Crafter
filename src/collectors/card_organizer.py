from pathlib import Path
from typing import Dict, List, Set
import json
from database.card_database import CardDatabase

class CardOrganizer:
    """Organizes card data by Oracle identity and printings"""
    
    def __init__(self, data_dir: str = "data/processed"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.database = CardDatabase()
        
    def organize_cards(self, raw_cards: List[Dict]) -> Dict:
        """Organize cards by Oracle ID with their printings"""
        print("Organizing cards by Oracle identity...")
        
        # Update database
        self.database.update_from_scryfall(raw_cards)
        
        # Return organized view
        return self.database.cards
    
    def save_organized_cards(self, oracle_cards: Dict):
        """Save organized card data"""
        # Save complete organized data
        organized_file = self.data_dir / "cards_organized.json"
        with open(organized_file, 'w', encoding='utf-8') as f:
            json.dump(oracle_cards, f, indent=2)
        
        # Create format-specific views
        self._create_format_views(oracle_cards)
        
    def _create_format_views(self, oracle_cards: Dict):
        """Create format-specific card views"""
        formats = ['standard', 'commander', 'modern', 'legacy', 'vintage', 'pauper']
        format_cards = {fmt: {} for fmt in formats}
        
        for oracle_id, card in oracle_cards.items():
            for fmt in formats:
                legality = card['legalities'].get(fmt)
                if legality in ['legal', 'restricted']:
                    # Find the newest printing that's legal in this format
                    legal_printings = [
                        p for p in card['printings']
                        if self._is_printing_legal_in_format(p, fmt)
                    ]
                    
                    if legal_printings:
                        # Sort by release date to get newest printing
                        newest_printing = sorted(
                            legal_printings,
                            key=lambda x: x['released_at'],
                            reverse=True
                        )[0]
                        
                        # Create format-specific card entry
                        format_cards[fmt][oracle_id] = {
                            **card,  # Base card data
                            'newest_printing': newest_printing
                        }
        
        # Save format-specific views
        for fmt, cards in format_cards.items():
            format_file = self.data_dir / f"cards_{fmt}_view.json"
            with open(format_file, 'w', encoding='utf-8') as f:
                json.dump(cards, f, indent=2)
            print(f"Saved {len(cards)} {fmt} cards")
    
    def _is_printing_legal_in_format(self, printing: Dict, format_name: str) -> bool:
        """Check if a specific printing is legal in a format"""
        if format_name == 'standard':
            # For Standard, check set legality
            return printing['set'] in self._get_standard_sets()
        return True  # For other formats, any printing is fine if Oracle card is legal
    
    def _get_standard_sets(self) -> Set[str]:
        """Get current Standard-legal set codes"""
        try:
            with open(self.data_dir.parent / "raw/standard_sets.json", 'r') as f:
                sets = json.load(f)
                return {s['code'] for s in sets}
        except FileNotFoundError:
            return set() 