from typing import List, Set
from dataclasses import dataclass
from enum import Enum

class ColorIdentity(Enum):
    WHITE = 'W'
    BLUE = 'U'
    BLACK = 'B'
    RED = 'R'
    GREEN = 'G'

@dataclass
class DeckTheme:
    name: str
    description: str
    key_cards: List[str]
    key_keywords: List[str]
    colors: Set[ColorIdentity] 