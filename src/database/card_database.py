import sqlite3
from pathlib import Path
import json
import hashlib
from typing import Dict, Optional, List
from datetime import datetime

class CardDatabase:
    """SQLite database for card information"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Use data directory for processed/compiled data
            db_path = Path("data/cards.db")
        else:
            db_path = Path(db_path)
            
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
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
            
            # Version tracking table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS version_info (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
    
    def _compute_cache_hash(self, cache_dir: Path) -> str:
        """Compute a hash of all set files in cache to track changes"""
        hasher = hashlib.sha256()
        sets_dir = cache_dir / "scryfall/sets"
        
        if not sets_dir.exists():
            return ""
            
        # Hash the metadata of all set files
        for set_file in sorted(sets_dir.glob("*.json")):
            stat = set_file.stat()
            # Include filename, size and modification time in hash
            file_info = f"{set_file.name}:{stat.st_size}:{stat.st_mtime}"
            hasher.update(file_info.encode())
            
        return hasher.hexdigest()
    
    def needs_update(self, cache_dir: Path) -> bool:
        """Check if database needs to be updated based on cache state"""
        current_hash = self._compute_cache_hash(cache_dir)
        if not current_hash:
            return True
            
        cursor = self.conn.execute(
            "SELECT value FROM version_info WHERE key = 'cache_hash'"
        )
        stored_hash = cursor.fetchone()
        
        return not stored_hash or stored_hash[0] != current_hash
    
    def load_from_cache(self, cache_dir: Path):
        """Load card data from Scryfall cache if needed"""
        if not self.needs_update(cache_dir):
            print("Database is up to date with cache")
            return
            
        print("Loading cards from cache...")
        sets_dir = cache_dir / "scryfall/sets"
        
        if not sets_dir.exists():
            raise FileNotFoundError(f"Cache directory not found: {sets_dir}")
        
        # Start a transaction for faster inserts
        with self.conn:
            # Clear existing data
            self.conn.execute("DELETE FROM cards")
            
            # Process each set file
            for set_file in sets_dir.glob("*.json"):
                try:
                    with open(set_file, 'r', encoding='utf-8') as f:
                        cards = json.load(f)
                        
                    for card in cards:
                        # Skip non-primary card faces for double-faced cards
                        if card.get('layout') in ['transform', 'modal_dfc'] and not card.get('is_front', True):
                            continue
                            
                        # Extract mana production from oracle text
                        produces_mana = self._extract_mana_production(card)
                        
                        self.conn.execute("""
                            INSERT OR REPLACE INTO cards (
                                name, mana_cost, cmc, type_line, oracle_text,
                                color_identity, is_land, produces_mana, layout
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            card['name'],
                            card.get('mana_cost'),
                            card.get('cmc', 0),
                            card.get('type_line', ''),
                            card.get('oracle_text', ''),
                            ','.join(card.get('color_identity', [])),
                            'Land' in card.get('type_line', ''),
                            ','.join(produces_mana),
                            card.get('layout', 'normal')
                        ))
                        
                except Exception as e:
                    print(f"Error processing {set_file}: {e}")
            
            # Update version info
            cache_hash = self._compute_cache_hash(cache_dir)
            self.conn.execute(
                "INSERT OR REPLACE INTO version_info (key, value) VALUES (?, ?)",
                ("cache_hash", cache_hash)
            )
            self.conn.execute(
                "INSERT OR REPLACE INTO version_info (key, value) VALUES (?, ?)",
                ("last_update", datetime.now().isoformat())
            )
    
    def _extract_mana_production(self, card: Dict) -> List[str]:
        """Extract what colors of mana this card can produce"""
        produces_mana = set()
        
        # Check if it's a basic land
        type_line = card.get('type_line', '').lower()
        if 'basic land' in type_line:
            if 'plains' in type_line: produces_mana.add('W')
            if 'island' in type_line: produces_mana.add('U')
            if 'swamp' in type_line: produces_mana.add('B')
            if 'mountain' in type_line: produces_mana.add('R')
            if 'forest' in type_line: produces_mana.add('G')
        
        # Check produced_mana field
        if 'produced_mana' in card:
            produces_mana.update(card['produced_mana'])
        
        return sorted(list(produces_mana))
    
    def get_card(self, card_name: str) -> Optional[Dict]:
        """Get card information from database"""
        try:
            with self.conn as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT name, cmc, type_line, oracle_text, color_identity, 
                           mana_cost, produces_mana, is_land
                    FROM cards 
                    WHERE name = ?
                """, (card_name,))
                row = cursor.fetchone()
                
                if row:
                    return {
                        'name': row[0],
                        'cmc': row[1],
                        'type_line': row[2],
                        'oracle_text': row[3],
                        'color_identity': row[4],
                        'mana_cost': row[5],
                        'produces_mana': row[6],
                        'is_land': bool(row[7])
                    }
                return None
                
        except Exception as e:
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