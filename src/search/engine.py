from pathlib import Path
from typing import List, Optional

from src.search.indexer import CardIndexer
from src.search.models import CardResult, PrintingInfo

class CardSearchEngine:
    """Magic card search engine"""
    
    def __init__(self, cache_dir: str = "cache/scryfall"):
        self.cache_dir = Path(cache_dir)
        self.indexer = CardIndexer(self.cache_dir)
        
        # Build indexes
        print("Building search indexes...")
        indexes = self.indexer.build_indexes()
        
        self.oracle_texts = indexes['oracle_texts']
        self.oracle_to_prints = indexes['oracle_to_prints']
        self.name_to_oracle = indexes['name_to_oracle']
        self.oracle_to_name = indexes['oracle_to_name']
        
        print(f"Indexed {len(self.oracle_texts)} unique cards")
        print(f"Found {sum(len(prints) for prints in self.oracle_to_prints.values())} total printings")
    
    def search_text(self, query: str) -> List[CardResult]:
        """Search for cards containing specific text"""
        query = query.lower()
        results = []
        
        for oracle_id, oracle_text in self.oracle_texts.items():
            if oracle_text and query in oracle_text.lower():
                results.append(CardResult(
                    name=self.oracle_to_name[oracle_id],
                    oracle_id=oracle_id,
                    oracle_text=oracle_text,
                    printings=sorted(
                        self.oracle_to_prints[oracle_id],
                        key=lambda x: x.released_at
                    )
                ))
        
        return sorted(results, key=lambda x: x.name)
    
    def find_card(self, card_name: str) -> Optional[CardResult]:
        """Find a specific card by name"""
        oracle_id = self.name_to_oracle.get(card_name.lower())
        if not oracle_id:
            return None
            
        return CardResult(
            name=card_name,
            oracle_id=oracle_id,
            oracle_text=self.oracle_texts[oracle_id],
            printings=sorted(
                self.oracle_to_prints[oracle_id],
                key=lambda x: x.released_at
            )
        ) 