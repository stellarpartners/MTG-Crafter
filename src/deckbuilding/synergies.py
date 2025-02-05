from typing import List, Dict, Set
from collections import defaultdict

class SynergyDetector:
    def __init__(self):
        self.synergy_patterns = {
            'sacrifice': {
                'providers': ['sacrifice', 'sacrifices', 'sacrificed'],
                'payoffs': ['whenever a creature dies', 'whenever a permanent you control is put into a graveyard']
            },
            'tokens': {
                'providers': ['create', 'token', 'tokens'],
                'payoffs': ['for each creature', 'number of creatures']
            },
            # Add more patterns...
        }
    
    def find_synergies(self, card_text: str) -> List[Dict]:
        """Find synergy patterns in card text"""
        synergies = []
        
        for category, patterns in self.synergy_patterns.items():
            # Check if card provides synergy
            if any(p in card_text.lower() for p in patterns['providers']):
                synergies.append({
                    'type': 'provider',
                    'category': category
                })
            
            # Check if card pays off synergy
            if any(p in card_text.lower() for p in patterns['payoffs']):
                synergies.append({
                    'type': 'payoff',
                    'category': category
                })
        
        return synergies 