from typing import List, Dict, Optional
from .card import Card

class Deck:
    """Represents a Magic: The Gathering deck"""
    
    def __init__(self, format_name: str):
        self.format = format_name
        self.cards: List[Card] = []
        self.sideboard: List[Card] = []
        self.commander: Optional[Card] = None  # For Commander format
        self.companion: Optional[Card] = None  # For companion mechanics
        
    def add_card(self, card: Card, count: int = 1, to_sideboard: bool = False):
        """Add card(s) to deck or sideboard"""
        target = self.sideboard if to_sideboard else self.cards
        for _ in range(count):
            target.append(card)
    
    def validate(self) -> List[str]:
        """Validate deck against format rules"""
        errors = []
        
        # Check deck size
        if self.format == "commander" and len(self.cards) != 100:
            errors.append("Commander decks must be exactly 100 cards")
        elif self.format == "standard" and len(self.cards) < 60:
            errors.append("Standard decks must be at least 60 cards")
            
        # Check card limits
        card_counts = {}
        for card in self.cards:
            card_counts[card.name] = card_counts.get(card.name, 0) + 1
            if card_counts[card.name] > 4 and card.name != "Basic Land":
                errors.append(f"Too many copies of {card.name}")
                
        return errors
    
    def get_statistics(self) -> Dict:
        """Calculate deck statistics"""
        return {
            'total_cards': len(self.cards),
            'mana_curve': self._calculate_mana_curve(),
            'color_distribution': self._calculate_colors(),
            'average_cmc': self._calculate_average_cmc()
        } 