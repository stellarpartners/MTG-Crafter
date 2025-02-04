from typing import Dict, List, Optional
from .card import Card

class Collection:
    """Represents a user's Magic: The Gathering collection"""
    
    def __init__(self):
        self.cards: Dict[str, Dict] = {}  # Card ID -> Card details
        
    def add_card(self, card: Card, quantity: int = 1, 
                 condition: str = "NM", is_foil: bool = False):
        """Add a card to the collection"""
        if card.id not in self.cards:
            self.cards[card.id] = {
                'card': card,
                'copies': []
            }
            
        for _ in range(quantity):
            self.cards[card.id]['copies'].append({
                'condition': condition,
                'is_foil': is_foil
            })
    
    def can_build_deck(self, deck_list: List[Dict]) -> bool:
        """Check if a deck can be built from collection"""
        required_cards = {}
        for card_entry in deck_list:
            card_id = card_entry['card'].id
            required_cards[card_id] = required_cards.get(card_id, 0) + 1
            
        for card_id, quantity in required_cards.items():
            if card_id not in self.cards:
                return False
            if len(self.cards[card_id]['copies']) < quantity:
                return False
                
        return True
    
    def get_value(self) -> float:
        """Calculate total collection value"""
        total = 0.0
        for card_data in self.cards.values():
            card = card_data['card']
            for copy in card_data['copies']:
                price = card.prices['usd_foil'] if copy['is_foil'] else card.prices['usd']
                if price:
                    total += float(price)
        return total 