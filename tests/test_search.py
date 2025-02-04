from src.search import CardSearchEngine, CardResult, PrintingInfo

def test_zombie_search():
    """Test searching for cards with 'Zombie' in their text"""
    engine = CardSearchEngine()
    
    results = engine.search_text("Zombie")
    print(f"\nFound {len(results)} cards mentioning 'Zombie'")
    
    # Show first 5 results
    for card in results[:5]:
        print(f"\n{card.name}:")
        print(f"Oracle Text: {card.oracle_text}")
        print(f"Printings ({len(card.printings)} total):")
        for printing in card.printings[:3]:
            print(f"- {printing.set_name} ({printing.set_code.upper()})")
        if len(card.printings) > 3:
            print(f"  ... and {len(card.printings) - 3} more printings")

def test_specific_card():
    """Test finding a specific card by name"""
    engine = CardSearchEngine()
    
    card = engine.find_card("Lord of the Undead")
    if card:
        print(f"\n{card.name}")
        print(f"Oracle ID: {card.oracle_id}")
        print(f"Oracle Text: {card.oracle_text}")
        print("\nPrintings:")
        for printing in sorted(card.printings, key=lambda x: x.released_at):
            print(f"- {printing.set_name} ({printing.set_code.upper()})")
            print(f"  Released: {printing.released_at}")
            print(f"  Rarity: {printing.rarity}")
            if 'usd' in printing.prices:
                print(f"  Price: ${printing.prices['usd']}")

if __name__ == "__main__":
    test_zombie_search()
    test_specific_card() 