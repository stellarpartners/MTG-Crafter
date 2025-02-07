import argparse
from .deck_loader import MoxfieldLoader
from .analyzer import Manalysis

def main():
    parser = argparse.ArgumentParser(description='Manalysis - MTG deck mana analysis tool')
    parser.add_argument('deck_url', help='URL of the Moxfield deck to analyze')
    parser.add_argument('--simulations', type=int, default=1000,
                       help='Number of simulations to run (default: 1000)')
    
    args = parser.parse_args()
    
    # TODO: Initialize card_db
    card_db = None  # Placeholder until we implement the card database
    if card_db is None:
         print("Error: Card database not initialized. Please run 'python3 1.gather_data.py' to create the database.")
         return
    
    # Load deck from Moxfield
    loader = MoxfieldLoader(card_db)
    decklist = loader.load_from_url(args.deck_url)
    
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