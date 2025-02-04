from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict
import json

from src.search.models import PrintingInfo

class CardIndexer:
    """Handles building and maintaining card indexes"""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        
    def build_indexes(self):
        """Build all search indexes from card data"""
        indexes = {
            'oracle_texts': {},  # oracle_id -> oracle_text
            'oracle_to_prints': defaultdict(list),  # oracle_id -> [printings]
            'name_to_oracle': {},  # card_name -> oracle_id
            'oracle_to_name': {},  # oracle_id -> card_name
            'set_info': {}  # set_code -> set metadata
        }
        
        sets_dir = self.cache_dir / "sets"
        if not sets_dir.exists():
            print(f"No sets directory found at {sets_dir}")
            return indexes
            
        print("Loading sets...")
        set_count = 0
        card_count = 0
        
        for set_file in sorted(sets_dir.glob("*.json")):
            try:
                with open(set_file, 'r', encoding='utf-8') as f:
                    set_cards = json.load(f)
                
                set_code = set_file.stem
                if set_cards:
                    # Get set info from first card
                    first_card = set_cards[0]
                    indexes['set_info'][set_code] = {
                        'name': first_card['set_name'],
                        'code': set_code,
                        'card_count': len(set_cards),
                        'release_date': first_card['released_at']
                    }
                    
                    # Process all cards in set
                    for card in set_cards:
                        if 'oracle_id' not in card:
                            continue
                        self._index_card(card, indexes)
                        card_count += 1
                    
                    set_count += 1
                    if set_count % 10 == 0:
                        print(f"Processed {set_count} sets...")
                    
            except Exception as e:
                print(f"Error processing {set_file}: {e}")
        
        # Sort printings by release date
        for prints in indexes['oracle_to_prints'].values():
            prints.sort(key=lambda x: x.released_at)
        
        print(f"\nProcessed {set_count} sets")
        print(f"Found {card_count} total cards")
        print(f"Indexed {len(indexes['oracle_texts'])} unique cards")
            
        return indexes
    
    def _index_card(self, card: Dict, indexes: Dict):
        """Index a single card's data"""
        oracle_id = card['oracle_id']
        card_name = card['name']
        
        # Store oracle text
        if oracle_id not in indexes['oracle_texts']:
            indexes['oracle_texts'][oracle_id] = card.get('oracle_text', '')
        
        # Map names and IDs
        indexes['name_to_oracle'][card_name.lower()] = oracle_id
        indexes['oracle_to_name'][oracle_id] = card_name
        
        # Store printing info
        printing = PrintingInfo(
            id=card['id'],
            set_code=card['set'],
            set_name=card['set_name'],
            released_at=card['released_at'],
            rarity=card['rarity'],
            collector_number=card['collector_number'],
            prices=card.get('prices', {}),
            image_uris=card.get('image_uris', {})
        )
        indexes['oracle_to_prints'][oracle_id].append(printing) 