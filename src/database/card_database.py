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
        
        # Load name index
        name_index_file = self.data_dir / "name_index.json"
        if name_index_file.exists():
            with open(name_index_file, 'r', encoding='utf-8') as f:
                self.name_index = json.load(f)
        else:
            self.name_index = {}
    
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
        """Process raw Scryfall data into our database format"""
        print("\nProcessing card data...")
        
        # Clear existing data
        self.cards = {}
        self.printings = {}
        self.sets = {}
        self.oracle_ids = {}
        
        # First pass: Process sets
        for card in raw_cards:
            set_code = card['set']
            if set_code not in self.sets:
                self.sets[set_code] = {
                    'name': card['set_name'],
                    'card_count': 0,
                    'release_date': card.get('released_at'),
                    'set_type': card.get('set_type')
                }
        
        # Second pass: Process cards and printings
        with tqdm(total=len(raw_cards), desc="Processing cards") as pbar:
            for card in raw_cards:
                try:
                    # Get basic card info
                    card_name = card['name']
                    oracle_id = card['oracle_id']
                    scryfall_id = card['id']
                    set_code = card['set']
                    
                    # Store oracle ID mapping
                    self.oracle_ids[card_name.lower()] = oracle_id
                    
                    # Process card data if we haven't seen this oracle ID
                    if oracle_id not in self.cards:
                        self.cards[oracle_id] = {
                            'name': card_name,
                            'mana_cost': card.get('mana_cost', ''),
                            'cmc': card.get('cmc', 0),
                            'type_line': card.get('type_line', ''),
                            'oracle_text': card.get('oracle_text', ''),
                            'colors': card.get('colors', []),
                            'color_identity': card.get('color_identity', []),
                            'keywords': card.get('keywords', []),
                            'legalities': card.get('legalities', {}),
                            'printings': []  # Will store all printing IDs
                        }
                    
                    # Always process printing data
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
                    
                    # Store printing and update references
                    self.printings[scryfall_id] = printing
                    self.cards[oracle_id]['printings'].append(scryfall_id)
                    self.sets[set_code]['card_count'] += 1
                    
                    pbar.update(1)
                    
                except Exception as e:
                    print(f"\nError processing card: {e}")
                    print(f"Card data: {card}")
                    continue
        
        # Sort printings by release date for each card
        for card in self.cards.values():
            card['printings'].sort(
                key=lambda pid: self.printings[pid]['released_at'],
                reverse=True  # Most recent first
            )
        
        print(f"\nProcessed {len(self.cards):,} unique cards")
        print(f"Found {len(self.printings):,} total printings")
        print(f"Across {len(self.sets):,} sets")
        
        # Save processed data
        self.save_database()
    
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

    def build_name_index(self):
        """Build a comprehensive index of all card names and their printings"""
        print("\nBuilding card name index...")
        
        # Initialize the name index
        self.name_index = {}
        
        # First pass: Collect all unique names and their printings
        for oracle_id, card in self.cards.items():
            name = card['name'].lower()
            if name not in self.name_index:
                self.name_index[name] = {
                    'name': card['name'],  # Preserve original capitalization
                    'oracle_versions': {},  # Different Oracle texts over time
                    'printings': []  # All printings regardless of Oracle text
                }
        
        # Second pass: Process all printings and Oracle texts
        for printing_id, printing in self.printings.items():
            name = printing['card_name'].lower()
            oracle_id = self.oracle_ids[name]
            card = self.cards[oracle_id]
            
            # Add printing info
            printing_info = {
                'set': printing['set'],
                'set_name': printing['set_name'],
                'collector_number': printing['collector_number'],
                'rarity': printing['rarity'],
                'released_at': printing['released_at'],
                'prices': printing['prices'],
                'image_uris': printing['image_uris']
            }
            self.name_index[name]['printings'].append(printing_info)
            
            # Track Oracle text version
            oracle_text = card['oracle_text']
            if oracle_text not in self.name_index[name]['oracle_versions']:
                self.name_index[name]['oracle_versions'][oracle_text] = {
                    'first_printed': printing['released_at'],
                    'mana_cost': card['mana_cost'],
                    'type_line': card['type_line'],
                    'oracle_text': oracle_text,
                    'colors': card['colors'],
                    'color_identity': card['color_identity'],
                    'legalities': card['legalities'],
                    'sets': []
                }
            self.name_index[name]['oracle_versions'][oracle_text]['sets'].append(printing['set'])
        
        # Sort printings by release date
        for card_data in self.name_index.values():
            card_data['printings'].sort(key=lambda x: x['released_at'])
            
            # Sort Oracle versions by first printing date
            card_data['oracle_versions'] = dict(
                sorted(
                    card_data['oracle_versions'].items(),
                    key=lambda x: x[1]['first_printed']
                )
            )
        
        print(f"Indexed {len(self.name_index)} unique card names")
        
        # Ensure database directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Save the index
        with open(self.data_dir / "name_index.json", 'w') as f:
            json.dump(self.name_index, f, indent=2) 