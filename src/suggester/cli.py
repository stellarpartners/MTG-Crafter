import argparse
from typing import Dict
from src.database.card_database import CardDatabase
from src.collectors.data_engine import DataEngine
from .core import CardSuggester

def main():
    """Interactive CLI for card suggestions"""
    parser = argparse.ArgumentParser(description='Find cheaper card alternatives')
    parser.add_argument('--max-mv', type=int, 
                       help='Maximum mana value for alternatives')
    parser.add_argument('--threshold', type=float, default=0.6,
                       help='Similarity threshold (0-1)')
    
    args = parser.parse_args()
    
    # Get card name interactively
    card_name = input("\nEnter card name to find alternatives for: ").strip()
    
    # Initialize database
    engine = DataEngine()
    card_db = engine.database
    
    # Get target card
    target_card = card_db.get_card(card_name)
    if not target_card:
        print(f"\nError: Card '{card_name}' not found in database")
        return
    
    # Find alternatives
    suggester = CardSuggester(card_db)
    alternatives = suggester.find_alternatives(
        target_card, 
        max_mv=args.max_mv or target_card.get('mana_value', 0)
    )
    
    # Filter by threshold
    filtered = [a for a in alternatives if a['similarity'] >= args.threshold]
    
    # Print results
    print(f"\nAlternatives for {card_name} (MV {target_card.get('mana_value', '?')}):")
    if not filtered:
        print("\nNo suitable alternatives found")
        return
        
    for alt in filtered[:5]:  # Show top 5
        card = alt['card']
        print(f"\n{card['name']} (MV {card.get('mana_value', '?')})")
        print(f"  Similarity: {alt['similarity']:.1%}")
        print(f"  Type: {card.get('type_line', 'Unknown')}")
        print(f"  Oracle Text: {card.get('oracle_text', 'No text')}")

if __name__ == '__main__':
    main() 