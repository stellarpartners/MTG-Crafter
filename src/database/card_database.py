from pathlib import Path
from typing import Dict, List, Set, Optional
import json
from datetime import datetime
from tqdm import tqdm

class CardDatabase:
    """Internal database of all Magic cards and their printings"""
    
    def __init__(self, data_dir: str = "data/database"):
        """Initialize the card database"""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize empty collections
        self.cards = {}
        self.printings = {}
        self.sets = {}
        self.oracle_ids = {}
        
        # Try to load existing database
        try:
            self.load_database()
        except (FileNotFoundError, json.JSONDecodeError):
            # If database doesn't exist or is corrupted, start with empty collections
            print("Starting with fresh database...")
            pass
    
    def load_database(self):
        """Load card data from files"""
        # Load printings
        printings_file = self.data_dir / "printings.json"
        if printings_file.exists():
            with open(printings_file, 'r', encoding='utf-8') as f:
                self.printings = json.load(f)
        
        # Load cards
        cards_file = self.data_dir / "cards.json"
        if cards_file.exists():
            with open(cards_file, 'r', encoding='utf-8') as f:
                self.cards = json.load(f)
        
        # Load sets
        sets_file = self.data_dir / "sets.json"
        if sets_file.exists():
            with open(sets_file, 'r', encoding='utf-8') as f:
                self.sets = json.load(f)
        
        # Load oracle IDs
        oracle_file = self.data_dir / "oracle_ids.json"
        if oracle_file.exists():
            with open(oracle_file, 'r', encoding='utf-8') as f:
                self.oracle_ids = json.load(f)
    
    def save_database(self):
        """Save the current database state"""
        with open(self.data_dir / "cards.json", 'w') as f:
            json.dump(self.cards, f, indent=2)
        with open(self.data_dir / "printings.json", 'w') as f:
            json.dump(self.printings, f, indent=2)
        with open(self.data_dir / "sets.json", 'w') as f:
            json.dump(self.sets, f, indent=2)
        with open(self.data_dir / "oracle_ids.json", 'w') as f:
            json.dump(self.oracle_ids, f, indent=2)
    
    def update_from_scryfall(self, raw_cards: List[Dict]):
        """Stage 1: Initial data load from Scryfall"""
        print("Loading raw card data...")
        
        # Store raw data for processing
        self.raw_cards = raw_cards
        print(f"Loaded {len(raw_cards):,} raw card entries")
        
        # Process the raw data
        self.process_raw_data()

    def process_raw_data(self):
        """Stage 2: Process and organize raw data"""
        print("\nProcessing card data...")
        
        # Clear existing data
        self.cards = {}
        self.printings = {}
        self.sets = {}
        self.oracle_ids = {}
        
        # Track sets we encounter
        encountered_sets = set()
        
        # First pass: Organize unique cards and sets
        print("Pass 1: Organizing unique cards and sets...")
        with tqdm(total=len(self.raw_cards), desc="Processing") as pbar:
            for card in self.raw_cards:
                if 'name' not in card:
                    pbar.update(1)
                    continue
                
                card_name = card['name']
                set_code = card['set']
                
                # Update set information
                if set_code not in self.sets:
                    self.sets[set_code] = {
                        'name': card['set_name'],
                        'code': set_code,
                        'released_at': card.get('released_at'),
                        'set_type': card.get('set_type'),
                        'card_count': 0
                    }
                encountered_sets.add(set_code)
                
                # Update unique card data
                if card_name not in self.cards:
                    self.cards[card_name] = {
                        'name': card_name,
                        'oracle_text': card.get('oracle_text'),
                        'mana_cost': card.get('mana_cost'),
                        'cmc': card.get('cmc', 0),
                        'color_identity': card.get('color_identity', []),
                        'keywords': card.get('keywords', []),
                        'type_line': card['type_line'],
                        'power': card.get('power'),
                        'toughness': card.get('toughness'),
                        'legalities': card['legalities'],
                        'printings': []  # List of scryfall_ids
                    }
                    self.oracle_ids[card_name.lower()] = card_name
                
                pbar.update(1)
        
        # Second pass: Process printings
        print("\nPass 2: Processing printings...")
        with tqdm(total=len(self.raw_cards), desc="Processing") as pbar:
            for card in self.raw_cards:
                if 'name' not in card:
                    pbar.update(1)
                    continue
                
                card_name = card['name']
                scryfall_id = card['id']
                set_code = card['set']
                
                # Add printing
                if scryfall_id not in self.printings:
                    printing = {
                        'card_name': card_name,
                        'set': set_code,
                        'set_name': card['set_name'],
                        'collector_number': card['collector_number'],
                        'rarity': card['rarity'],
                        'image_uris': card.get('image_uris', {}),
                        'prices': card.get('prices', {}),
                        'released_at': card['released_at']
                    }
                    self.printings[scryfall_id] = printing
                    self.cards[card_name]['printings'].append(scryfall_id)
                    self.sets[set_code]['card_count'] += 1
                
                pbar.update(1)
        
        # Update statistics
        self.stats = {
            'total_cards': len(self.raw_cards),
            'unique_cards': len(self.cards),
            'total_printings': len(self.printings),
            'total_sets': len(self.sets)
        }
        
        # Save processed data
        self.save_database()
        
        # Report results
        print(f"\nProcessing complete:")
        print(f"- {self.stats['unique_cards']:,} unique cards")
        print(f"- {self.stats['total_printings']:,} total printings")
        print(f"- {self.stats['total_sets']:,} sets")
    
    def get_card_by_name(self, name: str) -> Optional[Dict]:
        """Get card data by name"""
        oracle_id = self.oracle_ids.get(name.lower())
        if oracle_id:
            return self.cards[oracle_id]
        return None
    
    def get_printings(self, oracle_id: str) -> List[Dict]:
        """Get all printings of a card"""
        if oracle_id in self.cards:
            return [
                self.printings[printing_id] 
                for printing_id in self.cards[oracle_id]['printings']
            ]
        return []
    
    def get_legal_printings(self, oracle_id: str, format_name: str) -> List[Dict]:
        """Get legal printings of a card in a specific format"""
        if oracle_id not in self.cards:
            return []
            
        card = self.cards[oracle_id]
        if card['legalities'].get(format_name) not in ['legal', 'restricted']:
            return []
            
        printings = self.get_printings(oracle_id)
        
        if format_name == 'standard':
            # For Standard, only return printings from Standard-legal sets
            standard_sets = {
                code for code, data in self.sets.items()
                if data.get('set_type') in ['expansion', 'core']
                and self._is_set_in_standard(data)
            }
            return [p for p in printings if p['set'] in standard_sets]
            
        return printings
    
    def _is_set_in_standard(self, set_data: Dict) -> bool:
        """Check if a set is currently in Standard"""
        if not set_data.get('released_at'):
            return False
            
        release_date = datetime.fromisoformat(set_data['released_at'].replace('Z', '+00:00'))
        age = datetime.now() - release_date
        return age.days <= 545  # Roughly 18 months 