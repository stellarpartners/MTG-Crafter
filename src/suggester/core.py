from typing import Dict, List
from difflib import SequenceMatcher
from src.database.card_database import CardDatabase

class CardSuggester:
    """Suggests alternative cards based on similarity metrics"""
    
    def __init__(self, card_db: CardDatabase):
        self.card_db = card_db
    
    def find_alternatives(self, target_card: Dict, max_mv: int = None) -> List[Dict]:
        """Find alternative cards with similar functionality"""
        alternatives = []
        all_cards = self.card_db.get_all_cards()
        
        for card in all_cards:
            if card['name'] == target_card['name']:
                continue  # Skip the same card
                
            # Calculate similarity score (0-1)
            similarity = self._calculate_similarity(target_card, card)
            
            # Check if cheaper alternative
            if max_mv is not None and card.get('mana_value', 0) > max_mv:
                continue
                
            if similarity > 0.6:  # Adjust threshold as needed
                alternatives.append({
                    'card': card,
                    'similarity': similarity,
                    'mv_diff': card.get('mana_value', 0) - target_card.get('mana_value', 0)
                })
        
        # Sort by similarity then mana value difference
        return sorted(alternatives, key=lambda x: (-x['similarity'], x['mv_diff']))
    
    def _calculate_similarity(self, card_a: Dict, card_b: Dict) -> float:
        """Calculate similarity score between two cards"""
        # Type line similarity
        type_score = SequenceMatcher(
            None, 
            card_a.get('type_line', '').lower(), 
            card_b.get('type_line', '').lower()
        ).ratio()
        
        # Oracle text similarity
        text_score = SequenceMatcher(
            None,
            card_a.get('oracle_text', '').lower(),
            card_b.get('oracle_text', '').lower()
        ).ratio()
        
        # Mana cost similarity
        mv_diff = abs(card_a.get('mana_value', 0) - card_b.get('mana_value', 0))
        mv_score = 1 / (1 + mv_diff)  # Higher is better
        
        # Combine scores with weights
        return (0.4 * type_score) + (0.4 * text_score) + (0.2 * mv_score) 