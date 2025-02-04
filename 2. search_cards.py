from src.search import CardSearchEngine

def print_card_details(card):
    """Print formatted card details"""
    print(f"\n=== {card.name} ===")
    print(f"Oracle ID: {card.oracle_id}")
    print(f"Oracle Text: {card.oracle_text}")
    print("\nPrintings:")
    for printing in sorted(card.printings, key=lambda x: x.released_at):
        price = printing.prices.get('usd', 'N/A')
        print(f"- {printing.set_name} ({printing.set_code.upper()}) - {printing.rarity}")
        print(f"  Released: {printing.released_at}")
        print(f"  Price: ${price}")
        if printing.image_uris:
            print(f"  Art: {printing.image_uris.get('normal', 'N/A')}")
    print("=" * (len(card.name) + 8))

def main():
    engine = CardSearchEngine()
    
    while True:
        print("\nMTG Card Search")
        print("1. Search by card name")
        print("2. Search card text")
        print("3. Exit")
        
        choice = input("\nChoose an option (1-3): ")
        
        if choice == '1':
            name = input("\nEnter card name: ")
            card = engine.find_card(name)
            if card:
                print_card_details(card)
            else:
                print(f"\nNo card found with name: {name}")
                
        elif choice == '2':
            text = input("\nEnter text to search for: ")
            results = engine.search_text(text)
            print(f"\nFound {len(results)} cards containing '{text}'")
            
            if results:
                show_all = input("Show all results? (y/N): ").lower() == 'y'
                to_show = results if show_all else results[:5]
                
                for card in to_show:
                    print_card_details(card)
                
                if not show_all and len(results) > 5:
                    print(f"\n...and {len(results) - 5} more results")
                    
        elif choice == '3':
            break
            
        else:
            print("\nInvalid choice. Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main() 