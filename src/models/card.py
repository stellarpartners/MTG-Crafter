from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class Card:
    """Represents a Magic: The Gathering card"""
    
    id: str
    name: str
    mana_cost: Optional[str] = None
    cmc: float = 0.0
    colors: List[str] = None
    color_identity: List[str] = None
    type_line: str = ""
    oracle_text: Optional[str] = None
    power: Optional[str] = None
    toughness: Optional[str] = None
    keywords: List[str] = None
    legalities: Dict[str, str] = None
    
    def __post_init__(self):
        """Initialize default values for collections"""
        if self.colors is None:
            self.colors = []
        if self.color_identity is None:
            self.color_identity = []
        if self.keywords is None:
            self.keywords = []
        if self.legalities is None:
            self.legalities = {}
    
    @classmethod
    def from_scryfall_data(cls, data: Dict) -> 'Card':
        """Create a Card instance from Scryfall API data"""
        return cls(
            id=data['id'],
            name=data['name'],
            mana_cost=data.get('mana_cost'),
            cmc=data.get('cmc', 0.0),
            colors=data.get('colors', []),
            color_identity=data.get('color_identity', []),
            type_line=data.get('type_line', ''),
            oracle_text=data.get('oracle_text'),
            power=data.get('power'),
            toughness=data.get('toughness'),
            keywords=data.get('keywords', []),
            legalities=data.get('legalities', {})
        )
    
    def is_legal_in(self, format: str) -> bool:
        """Check if card is legal in given format"""
        return self.legalities.get(format.lower()) == 'legal'
    
    def is_commander(self) -> bool:
        """Check if card can be a commander"""
        if 'Legendary' not in self.type_line:
            return False
        return 'Creature' in self.type_line or 'can be your commander' in (self.oracle_text or '') 