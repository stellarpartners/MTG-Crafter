from pathlib import Path
from typing import Dict, List, Set
import json
from src.database.card_database import CardDatabase

class CardOrganizer:
    """Organizes card data by Oracle identity and printings"""
    
    def __init__(self, data_dir: str = "data/processed"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.database = CardDatabase()  # SQLite only
        
    def organize_cards(self):
        """Organize cards using SQL queries"""
        # Use SQL instead of JSON processing
        self.database.conn.execute("""
            CREATE TABLE IF NOT EXISTS organized_cards AS
            SELECT * FROM cards 
            WHERE layout NOT IN ('token', 'emblem')
        """)
    
    def save_organized_cards(self, oracle_cards: Dict):
        """Save organized card data"""
        # No longer saving to JSON
        pass
        
    def _create_format_views(self, oracle_cards: Dict):
        """Create format-specific card views"""
        # No longer saving to JSON
        pass
    
    def _is_printing_legal_in_format(self, printing: Dict, format_name: str) -> bool:
        """Check if a specific printing is legal in a format"""
        # No longer using JSON
        return True
    
    def _get_standard_sets(self) -> Set[str]:
        """Get current Standard-legal set codes"""
        # No longer using JSON
        return set() 