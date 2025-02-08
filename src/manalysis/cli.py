import argparse
from .deck_loader import DeckLoader
from .analyzer import Manalysis

def main():
    parser = argparse.ArgumentParser(description='Manalysis - MTG deck mana analysis tool')
    parser.add_argument('--clipboard', action='store_true',
                       help='Load deck from clipboard')
    parser.add_argument('--simulations', type=int, default=1000,
                       help='Number of simulations to run (default: 1000)')
    
    args = parser.parse_args()
    
    # TODO: Initialize card_db
    card_db = None  # Placeholder until we implement the card database
    if card_db is None:
         print("Error: Card database not initialized. Please run 'python3 1.gather_data.py' to create the database.")
         return
    
    # Load deck
    loader = DeckLoader(card_db)
    if args.clipboard:
        decklist = loader.load_from_clipboard()
    else:
        print("Please specify --clipboard to load a deck")
        return
    
    if not decklist:
        print("No deck loaded. Please check your input.")
        return
    
    # Run analysis
    analyzer = Manalysis(decklist, card_db)
    
    # Print results
    curve = analyzer.calculate_mana_curve()
    print("\nMana Curve:")
    print(curve)
    
    sim_results = analyzer.simulate_opening_hand(args.simulations)
    print("\nOpening Hand Analysis:")
    print(sim_results)

if __name__ == '__main__':
    main() 