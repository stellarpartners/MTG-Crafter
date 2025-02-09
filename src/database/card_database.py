import sqlite3
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime

class CardDatabase:
    """SQLite database for card information"""
    
    def __init__(self, db_path=None):
        # Set default path to data/database/cards.db
        if db_path is None:
            self.db_path = Path(__file__).parent.parent.parent / "data" / "database" / "cards.db"
        else:
            self.db_path = Path(db_path)
        
        # Create the parent directory if it doesn't exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database with UTF-8 encoding
        try:
            self.conn = sqlite3.connect(
                f'file:{self.db_path}?mode=rw', 
                uri=True,
                detect_types=sqlite3.PARSE_DECLTYPES,
                check_same_thread=False
            )
            self.conn.execute('PRAGMA encoding = "UTF-8"')
            self.conn.row_factory = sqlite3.Row
        except sqlite3.OperationalError as e:
            print(f"Error opening database: {str(e)}")
            print("Please ensure:")
            print("1. The database file exists at", self.db_path)
            print("2. You have proper read/write permissions")
            print("3. The file is a valid SQLite database")
            raise
        
        self.is_loaded = False
        self.create_tables()
        self.load_data()
    
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
            # Check if the database is already populated
            cursor = self.conn.execute("SELECT COUNT(*) FROM cards")
            count = cursor.fetchone()[0]
            if count > 0:
                self.is_loaded = True
                return
            
            # Load data from SQLite database
            self._load_from_sqlite()
            self.is_loaded = True
        except Exception as e:
            print(f"Error loading database: {str(e)}")
            self.is_loaded = False
    
    def _load_from_sqlite(self):
        """Load data from SQLite database"""
        # Implementation of SQLite loading logic
        pass
    
    def get_card(self, card_name: str) -> Optional[Dict]:
        """Get card information by name"""
        try:
            cursor = self.conn.execute("SELECT * FROM cards WHERE name = ?", (card_name,))
            row = cursor.fetchone()
            if row:
                return {
                    'name': row['name'],
                    'mana_value': row['cmc'],
                    'is_land': row['is_land'],
                    'type_line': row['type_line'],
                    'colors': row['color_identity'].split(',') if row['color_identity'] else [],
                    'mana_cost': row['mana_cost'],
                    'produces_mana': row['produces_mana'].split(',') if row['produces_mana'] else [],
                    'oracle_text': row['oracle_text']
                }
            else:
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