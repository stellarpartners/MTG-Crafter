from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class ManaCost:
    """Represents a card's mana cost"""
    total: int  # Total mana value
    colored: Dict[str, int]  # Colored mana requirements (e.g., {'W': 1, 'U': 2})
    generic: int  # Generic mana amount
    
    @classmethod
    def from_string(cls, cost_string: str) -> 'ManaCost':
        """Parse mana cost from string (e.g., '{2}{W}{U}'"""
        # TODO: Implement mana cost parsing
        pass

@dataclass
class Card:
    """Represents a Magic card with its mana properties"""
    name: str
    mana_cost: Optional[ManaCost]
    produces_mana: List[str]  # List of mana colors this card can produce
    is_land: bool
    
    @property
    def cmc(self) -> int:
        """Get converted mana cost / mana value"""
        return self.mana_cost.total if self.mana_cost else 0
