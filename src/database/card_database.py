import sqlite3
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime
import json
from tqdm import tqdm

class CardDatabase:
    """SQLite database for card information"""
    
    def __init__(self, db_path=None):
        # Simplified path handling
        self.db_path = Path(db_path) if db_path else (
            Path(__file__).parent.parent.parent / "data" / "database" / "cards.db"
        )
        
        print(f"Database location: {self.db_path.absolute()}")
        print(f"CardDatabase object ID: {id(self)}")
        
        # Create parent directories and empty file
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"Database parent directory exists: {self.db_path.parent.exists()}")
        print(f"Database file exists before touch: {self.db_path.exists()}")
        if not self.db_path.exists():
            print("Creating new database file...")
            self.db_path.touch()  # Create empty file
        print(f"Database file exists after touch: {self.db_path.exists()}")
        
        # Use proper connection string
        self.conn = None  # Initialize first
        self.connect()  # This should create the connection
        self.is_loaded = False  # Track database state
        
        if self.conn is None:
            raise RuntimeError("Connection lost after connect()!")
        
        # Initialize schema
        self.create_tables()
        self.is_loaded = True
    
    def connect(self):
        """Establish a connection to the SQLite database if not already connected."""
        if self.conn is None:
            try:
                print(f"Attempting to connect to: {self.db_path}")
                print(f"Database exists before connect: {self.db_path.exists()}")
                self.conn = sqlite3.connect(str(self.db_path))
                print("Connection successful")
                self.conn.execute('PRAGMA encoding = "UTF-8"')
                self.conn.row_factory = sqlite3.Row
                self._create_tables()  # Create tables immediately after connecting
            except Exception as e:
                print(f"FATAL: Failed to connect to database: {str(e)}")
                raise  # Re-raise the exception to stop execution
    
    def _create_tables(self):
        """Helper function to create tables"""
        if self.conn is None:
            raise RuntimeError("Database connection not established")
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS cards (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    mana_cost TEXT,
                    cmc REAL,
                    type_line TEXT,
                    oracle_text TEXT,
                    power TEXT,
                    toughness TEXT,
                    colors TEXT,
                    color_identity TEXT,
                    set_code TEXT,
                    rarity TEXT,
                    released_at TEXT,
                    updated_at TEXT,
                    is_land BOOLEAN DEFAULT 0,
                    produces_mana TEXT,
                    is_mana_rock BOOLEAN DEFAULT 0
                )
            """)
            
            # Sets table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS sets (
                    code TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    released_at TEXT,
                    card_count INTEGER,
                    set_type TEXT
                )
            """)
    
    def create_tables(self):
        """Create necessary database tables if they don't exist"""
        self.connect()
        
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS cards (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    mana_cost TEXT,
                    cmc REAL,
                    type_line TEXT,
                    oracle_text TEXT,
                    power TEXT,
                    toughness TEXT,
                    colors TEXT,
                    color_identity TEXT,
                    set_code TEXT,
                    rarity TEXT,
                    released_at TEXT,
                    updated_at TEXT,
                    is_land BOOLEAN DEFAULT 0,
                    produces_mana TEXT,
                    is_mana_rock BOOLEAN DEFAULT 0
                )
            """)
            
            # Sets table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS sets (
                    code TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    released_at TEXT,
                    card_count INTEGER,
                    set_type TEXT
                )
            """)
        
        print("create_tables() called, but tables should already exist.")
    
    def load_data(self):
        """Load data from JSON files into the database"""
        print("Loading data into database...")
        
        try:
            with self.conn:
                # Clear existing data
                self.conn.execute("DELETE FROM cards")
                self.conn.execute("DELETE FROM sets")
                
                # Load sets data
                sets_dir = Path(__file__).parent.parent.parent / "cache" / "scryfall" / "sets"
                set_files = list(sets_dir.glob("*.json"))
                
                if not set_files:
                    raise FileNotFoundError("No set files found in cache directory")
                
                total_cards = 0
                valid_sets = 0
                
                for set_file in tqdm(set_files, desc="Loading sets"):
                    try:
                        with open(set_file, 'r') as f:
                            set_data = json.load(f)
                            
                            # Validate root structure
                            if not isinstance(set_data, dict):
                                raise ValueError("Root is not a dictionary")
                                
                            if set_data.get('object') != 'set':
                                raise ValueError("Not a set object")
                                
                            # Required fields
                            required_fields = ['code', 'name', 'data']
                            for field in required_fields:
                                if field not in set_data:
                                    raise ValueError(f"Missing required field: {field}")
                                    
                            # Validate cards data
                            if not isinstance(set_data['data'], list):
                                raise ValueError("Card data is not a list")
                                
                            # Insert set info
                            self.conn.execute("""
                                INSERT OR REPLACE INTO sets 
                                (code, name, released_at, card_count, set_type)
                                VALUES (?, ?, ?, ?, ?)
                            """, (
                                set_data['code'],
                                set_data['name'],
                                set_data.get('released_at'),
                                len(set_data['data']),
                                set_data.get('set_type', 'unknown')
                            ))
                            
                            # Insert cards
                            cards_inserted = self._insert_cards(set_data['data'])
                            total_cards += cards_inserted
                            valid_sets += 1
                            
                    except Exception as e:
                        print(f"Invalid set file {set_file.name}: {str(e)}")
                        continue
                            
                print(f"\nDatabase loaded:")
                print(f"- Valid sets processed: {valid_sets}/{len(set_files)}")
                print(f"- Total cards inserted: {total_cards}")
                self.is_loaded = True
                
        except Exception as e:
            print(f"Fatal error loading data: {str(e)}")
            self.conn.rollback()
            raise
    
    def _insert_cards(self, cards):
        inserted = 0
        for card in cards:
            try:
                # Check for required fields
                if not all(key in card for key in ['name', 'set', 'rarity']):
                    print(f"Skipping invalid card: {card.get('name')}")
                    continue
                    
                # Insert into database
                self.conn.execute("""
                    INSERT INTO cards (
                        id, name, mana_cost, cmc, type_line,
                        oracle_text, power, toughness, colors,
                        color_identity, set_code, rarity, released_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    card['id'],
                    card['name'],
                    card.get('mana_cost', ''),
                    card.get('cmc', 0),
                    card['type_line'],
                    card.get('oracle_text', ''),
                    card.get('power', ''),
                    card.get('toughness', ''),
                    json.dumps(card.get('colors', [])),
                    json.dumps(card.get('color_identity', [])),
                    card['set'],
                    card['rarity'],
                    card['released_at'],
                    card.get('updated_at', card['released_at'])
                ))
                inserted += 1
            except sqlite3.IntegrityError:
                continue  # Skip duplicates
        
        if inserted < len(cards):
            print(f"Inserted {inserted}/{len(cards)} cards (duplicates skipped)")
        
        return inserted
    
    def get_card(self, card_name: str) -> Optional[Dict]:
        """Get card information by name"""
        try:
            cursor = self.conn.execute("""
                SELECT name, cmc, type_line, oracle_text, 
                       color_identity, mana_cost, produces_mana, is_land
                FROM cards 
                WHERE name = ? COLLATE NOCASE
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
        db_max_date_str = cursor.fetchone()[0]
        
        scryfall_file = Path(__file__).parent.parent.parent / "cache" / "scryfall" / "metadata.json"
        if not scryfall_file.exists():
            return True
            
        with open(scryfall_file, 'r') as f:
            metadata = json.load(f)
            scryfall_max_date_str = metadata.get('last_update')
            
        # Handle null dates
        if not db_max_date_str or not scryfall_max_date_str:
            return True
        
        # Convert to datetime objects
        db_max_date = datetime.fromisoformat(db_max_date_str)
        scryfall_max_date = datetime.fromisoformat(scryfall_max_date_str)
        
        return scryfall_max_date > db_max_date 