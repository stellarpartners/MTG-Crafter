#!/usr/bin/env python3
"""
Manalysis - Interactive tool for Magic: The Gathering mana analysis
"""

from src.manalysis.deck_loader import DeckLoader
from src.manalysis.analyzer import Manalysis
from src.database.card_database import CardDatabase
from pathlib import Path
from typing import Dict
import sqlite3

def show_analysis_menu(analyzer: Manalysis, decklist: Dict[str, int]):
    """Display analysis menu and handle input"""
    while True:
        print("\nAnalysis Options:")
        print("1. Show Mana Curve")
        print("2. Show Color Distribution")
        print("3. Simulate Opening Hands")
        print("4. Check Casting Probabilities")
        print("0. Return to Main Menu")
        
        choice = input("\nSelect an option (0-4): ")
        
        if choice == "0":
            return
        elif choice == "1":
            display_mana_curve(analyzer)
        elif choice == "2":
            display_color_distribution(analyzer)
        elif choice == "3":
            run_simulation(analyzer)
        elif choice == "4":
            check_casting_probabilities(analyzer)
        else:
            print("Invalid choice, please try again")

def display_mana_curve(analyzer: Manalysis):
    """Display formatted mana curve analysis"""
    curve = analyzer.calculate_mana_curve()
    print("\nMana Curve Analysis:")
    print("=" * 40)
    print(f"Average MV: {curve['average_mana_value']:.2f}")
    print(f"Median MV: {curve['median_mana_value']}")
    print("\nMana Value Distribution:")
    print(curve['visualization'])

def display_color_distribution(analyzer: Manalysis):
    """Display color distribution analysis"""
    colors = analyzer.analyze_color_distribution()
    print("\nColor Distribution:")
    print("=" * 40)
    for color, data in colors.items():
        print(f"{color}: {data['percentage']:.1f}% ({data['count']} cards)")

def run_simulation(analyzer: Manalysis):
    """Run and display opening hand simulation"""
    try:
        num_sims = int(input("How many simulations? (100-10000): "))
        results = analyzer.analyze_opening_hands(num_sims)
        print("\nSimulation Results:")
        print("=" * 40)
        print(f"Average lands in opening hand: {results['average_lands']:.2f}")
        print(f"No land probability: {results['no_land_percentage']:.1f}%")
    except ValueError:
        print("Invalid input. Please enter a number.")

def check_casting_probabilities(analyzer: Manalysis):
    """Display casting probability analysis"""
    try:
        num_sims = int(input("How many simulations? (100-1000): "))
        results = analyzer.analyze_casting_sequence(num_sims)
        print("\nCasting Probabilities:")
        print("=" * 40)
        for card, prob in results['cast_probability'].items():
            print(f"{card}: {prob*100:.1f}% chance by turn 10")
    except ValueError:
        print("Invalid input. Please enter a number.")

def main():
    print("Welcome to Manalysis!")
    print("=" * 40)
    
    # Initialize and validate database
    db = CardDatabase()
    if not validate_database(db):
        return

    loader = DeckLoader(db)
    main_menu_loop(loader, db)

def validate_database(db: CardDatabase) -> bool:
    """Ensure database exists and contains data"""
    try:
        print(f"\nDatabase path: {db.db_path}")
        print(f"Database exists: {db.db_path.exists()}")
        
        if not db.db_path.exists():
            print("Error: Database not found. Run gather_data.py first.")
            return False
            
        # Use a fresh connection to avoid threading issues
        with sqlite3.connect(f'file:{db.db_path}?mode=ro', uri=True) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM cards")
            count = cursor.fetchone()[0]
            print(f"Total cards in database: {count}")
            
            if count == 0:
                print("Error: Database empty. Run gather_data.py first.")
                return False
        return True
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False

def main_menu_loop(loader: DeckLoader, db: CardDatabase):
    """Handle main menu interactions"""
    while True:
        print("\nMain Menu:")
        print("1. Load Saved Deck")
        print("2. Import New Deck from Clipboard")
        print("3. List Saved Decks")
        print("0. Exit")
        
        choice = input("\nSelect an option (0-3): ").strip()
        
        if choice == "0":
            print("\nGoodbye!")
            break
        elif choice == "1":
            handle_saved_deck(loader, db)
        elif choice == "2":
            handle_new_deck(loader, db)
        elif choice == "3":
            list_saved_decks(loader)
        else:
            print("Invalid choice. Please try again.")

def handle_saved_deck(loader: DeckLoader, db: CardDatabase):
    """Handle saved deck selection and analysis"""
    decks = loader.list_saved_decks()
    if not decks:
        print("No saved decks found.")
        return

    print("\nSaved Decks:")
    for i, deck in enumerate(decks, 1):
        print(f"{i}. {deck['name']} ({deck['commander']})")

    try:
        selection = int(input("\nEnter deck number: ")) - 1
        deck_data = decks[selection]
        decklist = loader.load_deck(deck_data['id'])
        analyzer = Manalysis(decklist, db)
        show_analysis_menu(analyzer, decklist)
    except (ValueError, IndexError):
        print("Invalid selection.")

def handle_new_deck(loader: DeckLoader, db: CardDatabase):
    """Handle new deck import and analysis"""
    print("\nPaste decklist (format: 1x Card Name)")
    decklist = loader.load_from_clipboard()
    
    if not decklist:
        print("No valid decklist found.")
        return
        
    print(f"\nLoaded {sum(decklist.values())} cards")
    analyzer = Manalysis(decklist, db)
    show_analysis_menu(analyzer, decklist)
    
    if input("\nSave this deck? (y/n): ").lower() == 'y':
        name = input("Enter deck name: ").strip()
        if name:
            loader.save_deck(decklist, name)
            print("Deck saved.")

def list_saved_decks(loader: DeckLoader):
    """Display list of saved decks"""
    decks = loader.list_saved_decks()
    if not decks:
        print("No saved decks found.")
        return
        
    print("\nSaved Decks:")
    for deck in decks:
        print(f"- {deck['name']} ({deck['commander']})")

if __name__ == '__main__':
    main() 