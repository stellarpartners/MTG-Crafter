from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime

@dataclass
class PrintingInfo:
    id: str
    set_code: str
    set_name: str
    released_at: str
    rarity: str
    collector_number: str
    prices: Dict[str, str]
    image_uris: Dict[str, str]

@dataclass
class CardResult:
    name: str
    oracle_id: str
    oracle_text: str
    printings: List[PrintingInfo] 