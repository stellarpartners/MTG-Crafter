import sqlite3
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime
import json
from tqdm import tqdm
import requests
from src.utils.json_validator import JSONValidator

class CardDatabase:
    """SQLite database for card information"""
    
    # Add version constants
    VERSION_MAJOR = 1
    VERSION_MINOR = 2
    SCHEMA_VERSION = 1.1
    
    @property
    def version(self) -> str:
        return f"{self.VERSION_MAJOR}.{self.VERSION_MINOR}"
    
    @property 
    def version_major(self) -> int:
        return self.VERSION_MAJOR
    
    @property
    def version_minor(self) -> int:
        return self.VERSION_MINOR
    
    def __init__(self, db_path=None):
        # Simplified path handling
        self.db_path = Path(db_path) if db_path else (
            Path(__file__).parent.parent.parent / "data" / "database" / "cards.db"
        )
        
        if not self.db_path.exists():
            print("Creating new database file...")
            self.db_path.touch()  # Create empty file
        
        # Use proper connection string
        self.conn = None  # Initialize first
        self.connect()  # This should create the connection
        self.is_loaded = False  # Track database state
        
        if self.conn is None:
            raise RuntimeError("Connection lost after connect()!")
        
        # Initialize schema
        self.create_tables()
        
        # Only load data if database is empty
        if self._is_database_empty():
            print("Initial database setup - loading data from JSONs")
            self.load_data()
        else:
            print("Using existing database - JSON cache not required")
            
        self.is_loaded = True
    
    def connect(self):
        """Establish a connection to the SQLite database if not already connected."""
        if self.conn is None:
            try:
                self.conn = sqlite3.connect(str(self.db_path))
                self.conn.execute('PRAGMA encoding = "UTF-8"')
                self.conn.row_factory = sqlite3.Row
            except Exception as e:
                raise
    
    def create_tables(self):
        """Create tables if they don't exist"""
        try:
            with self.conn:
                # Drop existing tables to ensure schema is updated
                self.conn.execute("DROP TABLE IF EXISTS cards")
                self.conn.execute("DROP TABLE IF EXISTS sets")
                self.conn.execute("DROP TABLE IF EXISTS card_faces")
                self.conn.execute("DROP TABLE IF EXISTS keywords")
                self.conn.execute("DROP TABLE IF EXISTS legalities")
                self.conn.execute("DROP TABLE IF EXISTS prices")
                self.conn.execute("DROP TABLE IF EXISTS themes")
                self.conn.execute("DROP TABLE IF EXISTS rulings")

                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS sets (
                        code TEXT PRIMARY KEY,
                        name TEXT,
                        block_code TEXT,
                        block TEXT,
                        released_at TEXT,
                        set_type TEXT,
                        card_count INTEGER,
                        parent_set_code TEXT,
                        uri TEXT,
                        scryfall_uri TEXT,
                        search_uri TEXT
                    )
                """)
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS cards (
                        id TEXT PRIMARY KEY,
                        name TEXT,
                        mana_cost TEXT,
                        cmc REAL,
                        colors TEXT,
                        color_identity TEXT,
                        type_line TEXT,
                        oracle_text TEXT,
                        power TEXT,
                        toughness TEXT,
                        loyalty TEXT,
                        set_code TEXT,
                        rarity TEXT,
                        artist TEXT,
                        flavor_text TEXT,
                        frame TEXT,
                        full_art INTEGER,
                        textless INTEGER,
                        uri TEXT,
                        scryfall_uri TEXT,
                        border_crop TEXT,
                        image_url TEXT,
                        edhrec_rank INTEGER,
                        keywords TEXT
                    )
                """)
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS card_faces (
                        id TEXT PRIMARY KEY,
                        card_id TEXT,
                        face_name TEXT,
                        mana_cost TEXT,
                        cmc REAL,
                        colors TEXT,
                        type_line TEXT,
                        oracle_text TEXT,
                        power TEXT,
                        toughness TEXT,
                        loyalty TEXT,
                        image_url TEXT,
                        FOREIGN KEY (card_id) REFERENCES cards(id)
                    )
                """)
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS keywords (
                        card_id TEXT,
                        keyword TEXT,
                        FOREIGN KEY (card_id) REFERENCES cards(id),
                        PRIMARY KEY (card_id, keyword)
                    )
                """)
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS legalities (
                        card_id TEXT,
                        format TEXT,
                        legality TEXT,
                        FOREIGN KEY (card_id) REFERENCES cards(id),
                        PRIMARY KEY (card_id, format)
                    )
                """)
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS prices (
                        card_id TEXT,
                        date TEXT,
                        usd REAL,
                        usd_foil REAL,
                        eur REAL,
                        eur_foil REAL,
                        tix REAL,
                        FOREIGN KEY (card_id) REFERENCES cards(id),
                        PRIMARY KEY (card_id, date)
                    )
                """)
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS themes (
                        card_id TEXT,
                        theme TEXT,
                        FOREIGN KEY (card_id) REFERENCES cards(id),
                        PRIMARY KEY (card_id, theme)
                    )
                """)
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS rulings (
                        card_id TEXT,
                        source TEXT,
                        comment TEXT,
                        date TEXT,
                        FOREIGN KEY (card_id) REFERENCES cards(id),
                        PRIMARY KEY (card_id, source, comment, date)
                    )
                """)
                
            print("✅ Tables created successfully")
        except sqlite3.Error as e:
            print(f"❌ Error creating tables: {e} - SQL: {e.__traceback__.tb_frame.f_locals.get('sql')}")
    
    def load_data(self):
        """Load data from JSON files with enhanced error handling"""
        set_files = list(Path("cache/scryfall/sets").glob("*.json"))
        
        # Handle empty cache scenario
        if not set_files:
            print("⚠️ No cached set files found - run data collection first")
            self.is_loaded = False
            return
        
        # Existing loading logic...
        try:
            with self.conn:
                # Clear existing data
                self.conn.execute("DELETE FROM cards")
                self.conn.execute("DELETE FROM sets")
                
                # Load sets data
                total_cards = 0
                valid_sets = 0
                
                for set_file in tqdm(set_files, desc="Processing sets"):
                    try:
                        # Validate before processing
                        if not JSONValidator.validate_set_file(set_file):
                            print(f"Skipping invalid set file: {set_file.name}")
                            continue
                        
                        with open(set_file, 'r', encoding='utf-8') as f:
                            set_data = json.load(f)
                            
                        # Validate set structure before processing
                        if not isinstance(set_data, dict):
                            print(f"❌ Invalid set file {set_file.name} - root is not a dictionary")
                            continue
                            
                        if 'data' not in set_data or not isinstance(set_data['data'], list):
                            print(f"❌ Invalid set file {set_file.name} - missing data list")
                            continue
                            
                        # Process cards with individual validation
                        valid_cards = 0
                        for card in set_data['data']:
                            try:
                                # Existing card processing...
                                valid_cards += 1
                            except Exception as card_error:
                                print(f"⚠️ Skipping invalid card in {set_file.name}: {str(card_error)}")
                            
                        print(f"Processed {valid_cards}/{len(set_data['data'])} cards from {set_file.name}")
                        
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
                        
                    except json.JSONDecodeError as e:
                        print(f"❌ Corrupted JSON in {set_file.name}: {e}")
                        # Attempt repair
                        if self._attempt_repair(set_file):
                            print(f"Repaired {set_file.name}, please reload data")
                            
                print(f"\nDatabase loaded:")
                print(f"- Valid sets processed: {valid_sets}/{len(set_files)}")
                print(f"- Total cards inserted: {total_cards}")
                self.is_loaded = True
                
        except Exception as e:
            print(f"Fatal error loading data: {e}")
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
                        color_identity, set_code, rarity, artist, flavor_text, frame, full_art, textless, uri, scryfall_uri, border_crop, image_url, edhrec_rank, keywords
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    card.get('artist', ''),
                    card.get('flavor_text', ''),
                    card.get('frame', ''),
                    card.get('full_art', 0),
                    card.get('textless', 0),
                    card.get('uri', ''),
                    card.get('scryfall_uri', ''),
                    card.get('border_crop', ''),
                    card.get('image_url', ''),
                    card.get('edhrec_rank', 0),
                    json.dumps(card.get('keywords', []))
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

    def _is_database_empty(self) -> bool:
        """Check if database has any cards"""
        cursor = self.conn.execute("SELECT COUNT(*) FROM cards")
        return cursor.fetchone()[0] == 0

    def needs_update(self) -> bool:
        """Check updates using database-stored metadata instead of JSON files"""
        cursor = self.conn.execute("SELECT value FROM metadata WHERE key='scryfall_last_update'")
        db_last_update = cursor.fetchone()
        
        if not db_last_update:
            return True
            
        db_date = datetime.fromisoformat(db_last_update[0])
        
        # Get current Scryfall update date directly from API
        response = requests.get("https://api.scryfall.com/bulk/meta")
        response.raise_for_status()
        scryfall_date = datetime.fromisoformat(response.json()['updated_at'])
        
        return scryfall_date > db_date 

    def _attempt_repair(self, set_file: Path) -> bool:
        """Attempt to repair corrupted set files"""
        try:
            backup_path = set_file.with_suffix('.bak')
            set_file.replace(backup_path)
            
            with open(backup_path, 'r', encoding='utf-8') as f:
                data = f.read()
                
            # Simple repair attempts
            data = data.strip()
            if data[-1] != '}': 
                data += '}'
                
            repaired = json.loads(data)
            with open(set_file, 'w') as f:
                json.dump(repaired, f)
                
            return True
        except Exception as e:
            print(f"❌ Failed to repair {set_file.name}: {e}")
            return False 