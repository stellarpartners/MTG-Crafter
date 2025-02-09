from typing import Dict
from datetime import datetime
import json
import sqlite3
import pyperclip
import re
from pathlib import Path
from src.manalysis.analyzer import Manalysis
from src.collectors.data_engine import DataEngine

class DeckLoader:
    """Handles importing and saving decks"""
    
    def __init__(self, card_db):
        """Initialize loader with card database"""
        self.card_db = card_db
        self.commander = None
        self.data_dir = Path(__file__).parent.parent / "data"
        self.conn = sqlite3.connect(self.data_dir / "decks.db")
        
    def save_deck(self, decklist: Dict[str, int], deck_name: str) -> bool:
        """Save deck to database with proper error handling"""
        try:
            # Create saved_decks directory if it doesn't exist
            saved_dir = self.data_dir / "saved_decks"
            saved_dir.mkdir(parents=True, exist_ok=True)
            
            deck_path = saved_dir / f"{deck_name}.json"
            
            if deck_path.exists():
                print(f"Deck '{deck_name}' already exists!")
                return False
            
            deck_data = {
                "name": deck_name,
                "commander": self.commander,
                "cards": decklist,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            with open(deck_path, 'w') as f:
                json.dump(deck_data, f, indent=2)
            
            # Update database
            with self.conn:
                self.conn.execute("""
                    INSERT INTO decks (name, commander, file_path, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    deck_name,
                    self.commander,
                    str(deck_path),
                    deck_data['created_at'],
                    deck_data['updated_at']
                ))
            
            print(f"Deck '{deck_name}' saved successfully at {deck_path}")
            return True
        
        except sqlite3.IntegrityError:
            print(f"Deck name '{deck_name}' already exists in database!")
            return False
        except Exception as e:
            print(f"Error saving deck: {str(e)}")
            return False

    def load_from_clipboard(self) -> Dict[str, int]:
        """Load deck from clipboard with better validation"""
        try:
            clipboard = pyperclip.paste()
            if not clipboard:
                print("Clipboard is empty!")
                return {}
            
            decklist = {}
            # Improved pattern to handle various formats
            line_pattern = re.compile(r'(\d+)\s*(?:x|\X)?\s*([^#]+)')
            
            for line in clipboard.splitlines():
                line = line.strip()
                if not line:
                    continue
                
                match = line_pattern.match(line)
                if match:
                    quantity = int(match.group(1))
                    raw_name = match.group(2).strip()
                    
                    # Clean up name variations
                    card_name = re.sub(r'\s*[\(\[].*?[\)\]]', '', raw_name)  # Remove set codes
                    card_name = card_name.replace('’', "'")  # Normalize apostrophes
                    
                    # Try multiple lookup strategies
                    card = self.card_db.get_card(card_name)
                    if not card:
                        # Try removing special characters
                        clean_name = re.sub(r"[,'\-]", "", card_name)
                        card = self.card_db.get_card(clean_name)
                    if not card:
                        # Try case-insensitive search
                        card = self.card_db.search_cards(card_name)
                        if card:
                            card = card[0]
                    
                    if not card:
                        print(f"Warning: '{card_name}' not found in database - check spelling or update database")
                        continue
                    
                    decklist[card_name] = quantity
                
            return decklist
        
        except pyperclip.PyperclipException as e:
            print(f"Clipboard access error: {str(e)}")
            return {}
        except Exception as e:
            print(f"Unexpected error loading from clipboard: {str(e)}")
            return {}

    def _parse_deck_text(self, deck_text: str) -> Dict[str, int]:
        # Implementation of _parse_deck_text method
        pass

    def any_card_validation(self, card_name: str) -> bool:
        # Implementation of any_card_validation method
        pass

def run_analysis(decklist: Dict[str, int]):
    """Run mana analysis on a decklist"""
    print("[DEBUG] Initializing DataEngine")  # Debug
    engine = DataEngine()
    print("[DEBUG] Accessing database from DataEngine")  # Debug
    card_db = engine.database  # Access the CardDatabase object from DataEngine
    print(f"[DEBUG] Creating Manalysis with database: {card_db}")  # Debug
    analyzer = Manalysis(decklist, card_db)  # Pass the CardDatabase object directly
    
    # Perform analysis and print results
    print("[DEBUG] Calculating mana curve")  # Debug
    curve = analyzer.calculate_mana_curve()
    print("\nMana Value Statistics:")
    print("-" * 40)
    print(f"The average mana value of your deck is {curve['average_mana_value']:.2f} with lands and "
          f"{curve['average_mana_value_without_lands']:.2f} without lands.")
    print(f"The median mana value of your deck is {curve['median_mana_value']} with lands and "
          f"{curve['median_mana_value_without_lands']} without lands.")
    print(f"This deck's total mana value is {curve['total_mana_value']}.")
    
    # Add visualization
    print("\nCard Count by Mana Value:")
    print(f"{'-' * 40}")
    print(curve['visualization'])
    
    # Add curve health analysis
    print(f"\nCurve Health: {curve['curve_health']['status']}")
    print(curve['curve_health']['message'])
    print(f"Early game (0-2): {curve['curve_health']['distribution']['early_game']:.1f}%")
    print(f"Mid game (3-5): {curve['curve_health']['distribution']['mid_game']:.1f}%")
    print(f"Late game (6+): {curve['curve_health']['distribution']['late_game']:.1f}%")
    
    # Add detailed color statistics
    color_stats = curve['color_stats']
    print("\nDetailed Color Statistics:")
    print("-" * 40)
    print(f"Land cards: {color_stats['land_count']}")
    print(f"Non-land cards: {color_stats['non_land_count']}")
    
    for color in ['W', 'U', 'B', 'R', 'G', 'C']:
        print(f"\n{color}:")
        print(f"  {color_stats['non_land_cards'][color]} out of {color_stats['non_land_count']} non-land cards are {{{color}}}")
        print(f"  {color_stats['non_land_mana_symbols'][color]} out of {sum(color_stats['non_land_mana_symbols'].values())} mana symbols on non-land cards are {{{color}}}")
        print(f"  {color_stats['land_produces'][color]} out of {color_stats['land_count']} land cards produce {{{color}}}")
        print(f"  {color_stats['land_mana_symbols'][color]} out of {sum(color_stats['land_mana_symbols'].values())} mana symbols on lands produce {{{color}}}")
    
    # Add mana sources analysis
    mana_sources = curve['mana_sources']
    print("\nMana Sources Analysis:")
    print("-" * 40)
    print(f"Total mana sources: {mana_sources['total_sources']}")
    print("Breakdown by color:")
    for color, count in mana_sources['breakdown']['by_color'].items():
        print(f"{color}: {count}")
    
    # Add mana rock and mana dork statistics
    print("\nMana Rocks:")
    if mana_sources['mana_rocks']:
        for rock in mana_sources['mana_rocks']:
            print(f"  - {rock}")
    else:
        print("  No mana rocks found")
    
    print("\nMana Dorks:")
    if mana_sources['mana_dorks']:
        for dork in mana_sources['mana_dorks']:
            print(f"  - {dork}")
    else:
        print("  No mana dorks found")
    
    # Add mana discount analysis
    mana_discounts = curve['mana_discounts']
    print("\nMana Value Discounts:")
    if mana_discounts:
        for card_name, discount in mana_discounts.items():
            print(f"  - {card_name}: Original MV = {discount['original_mana_value']}, Reduced MV = {discount['reduced_mana_value']} ({discount['condition']})")
    else:
        print("  No mana value discounts found") 