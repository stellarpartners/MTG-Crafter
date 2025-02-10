import sqlite3
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime
import json

class CardDatabase:
    """SQLite database for card information"""
    
    def __init__(self, db_path=None):
        # Simplified path handling
        self.db_path = Path(db_path) if db_path else (
            Path(__file__).parent.parent.parent / "data" / "database" / "cards.db"
        )
        
        # Create parent directories
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Simplified connection setup
        self.conn = sqlite3.connect(f'file:{self.db_path}?mode=rwc', uri=True)
        self.conn.execute('PRAGMA encoding = "UTF-8"')
        self.conn.row_factory = sqlite3.Row
        
        # Initialize schema
        self.create_tables()
    
    def create_tables(self):
        """Create necessary database tables if they don't exist"""
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS cards (
                    name TEXT PRIMARY KEY,
                    mana_cost TEXT,
                    cmc INTEGER,
                    type_line TEXT,
                    oracle_text TEXT,
                    color_identity TEXT,
                    is_land BOOLEAN,
                    produces_mana TEXT,
                    layout TEXT
                )
            """)
    
    def load_data(self):
        """Load card data into the database"""
        try:
            self.is_loaded = True
        except Exception as e:
            print(f"Error loading database: {str(e)}")
            self.is_loaded = False
    
    def get_card(self, card_name: str) -> Optional[Dict]:
        """Get card information by name"""
        try:
            cursor = self.conn.execute("""
                SELECT name, cmc, type_line, oracle_text, 
                       color_identity, mana_cost, produces_mana, is_land
                FROM cards 
                WHERE name = ?
            """, (card_name,))
            row = cursor.fetchone()
            
            if row:
                return {
                    'name': row['name'],
                    'mana_value': row['cmc'],
                    'is_land': bool(row['is_land']),
                    'type_line': row['type_line'],
                    'colors': row['color_identity'].split(',') if row['color_identity'] else [],
                    'mana_cost': row['mana_cost'],
                    'produces_mana': row['produces_mana'].split(',') if row['produces_mana'] else [],
                    'oracle_text': row['oracle_text'],
                    'is_mana_rock': 'artifact' in row['type_line'].lower() 
                                   and row['produces_mana'] != ''
                }
            return None
        except Exception as e:
            print(f"Error getting card {card_name}: {str(e)}")
            return None
    
    def search_cards(self, query: str) -> List[sqlite3.Row]:
        """Search cards by name pattern"""
        cursor = self.conn.execute(
            "SELECT * FROM cards WHERE name LIKE ?",
            (f"%{query}%",)
        )
        return cursor.fetchall()
    
    def close(self):
        """Close database connection"""
        self.conn.close()
    
    def force_close(self):
        """Force close the database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def needs_update(self) -> bool:
        """Check if database needs updating based on Scryfall data"""
        cursor = self.conn.execute("SELECT MAX(updated_at) FROM cards")
        db_max_date = cursor.fetchone()[0]
        
        scryfall_file = Path(__file__).parent.parent.parent / "cache" / "scryfall" / "metadata.json"
        if not scryfall_file.exists():
            return True
            
        with open(scryfall_file, 'r') as f:
            metadata = json.load(f)
            scryfall_max_date = metadata.get('last_update')
            
        return scryfall_max_date and scryfall_max_date > db_max_date 