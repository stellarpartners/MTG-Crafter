from src.deckbuilding import DeckSuggester
from src.deckbuilding.training import TrainingPipeline
from typing import Dict, List, Optional

def print_header():
    print("\nMTG Deck Builder")
    print("================")

def show_main_menu() -> str:
    print("\nMain Menu:")
    print("1. Build New Deck")
    print("2. Browse Saved Decks")
    print("3. Setup/Update Models")
    print("4. Exit")
    return input("\nSelect an option (1-4): ")

def handle_setup() -> None:
    """Run first-time setup or update models
    
    Downloads required data and trains ML models.
    Provides options for:
    1. Fresh installation
    2. Update existing models
    3. Force retrain
    """
    print("\nSetup/Update Models")
    print("===================")
    
    print("\nThis will download card data and train models.")
    if input("\nContinue? (y/N): ").lower() == 'y':
        pipeline = TrainingPipeline()
        force = input("Force retrain existing models? (y/N): ").lower() == 'y'
        pipeline.run_pipeline(force_retrain=force)
        print("\nSetup complete! You can now use the deck builder.")
    
    input("\nPress Enter to continue...")

def handle_deck_building() -> None:
    """Handle deck building process
    
    Presents options to:
    1. Build around a commander
    2. Build from colors/themes
    3. Return to main menu
    
    Handles all user input and error cases.
    """
    try:
        suggester = DeckSuggester()
    except SystemExit:
        print("\nError: Unable to initialize deck builder. Please run setup first.")
        input("\nPress Enter to continue...")
        return
        
    print("\nDeck Building")
    print("=============")
    
    while True:
        print("\nBuild Method:")
        print("1. Build around a card")
        print("2. Build from colors/themes")
        print("3. Back to main menu")
        
        choice = input("\nSelect an option (1-3): ").strip()
        
        if choice == "3":
            break
        elif choice not in ["1", "2"]:
            print("\nInvalid choice")
            continue
            
        try:
            if choice == "1":
                # Build around a card
                while True:
                    card = input("\nEnter card name (or 'back' to return): ").strip()
                    if not card or card.lower() == 'back':
                        break
                    try:
                        suggestions = suggester.suggest_from_card(card)
                        if suggestions:
                            break
                    except ValueError as e:
                        print(f"\nError: {str(e)}")
                        continue
            else:
                # Get colors
                print("\nAvailable colors:")
                print("W - White")
                print("U - Blue")
                print("B - Black")
                print("R - Red")
                print("G - Green")
                colors = input("\nEnter colors (e.g. B G for Black-Green): ").upper().split()
                
                # Show themes
                available_themes = suggester.list_themes()
                print("\nAvailable Themes:")
                for i, theme in enumerate(available_themes, 1):
                    print(f"{i}. {theme}")
                
                # Get theme choices
                theme_nums = input("\nEnter theme numbers (space-separated): ").split()
                theme_choices = [available_themes[int(num)-1] for num in theme_nums]
                
                print(f"\nBuilding {'-'.join(colors)} deck with themes: {', '.join(theme_choices)}")
                suggestions = suggester.suggest_deck(colors, theme_choices)
        except Exception as e:
            print(f"\nError: {str(e)}")
            continue
        
        # Wait for user to review suggestions
        input("\nPress Enter to see deck suggestions...")
        show_deck_suggestions(suggestions, suggester)

def show_deck_suggestions(suggestions: Dict[str, List[Dict]], suggester: Optional[DeckSuggester] = None) -> None:
    """Display deck suggestions"""
    print("\nDeck Suggestions:")
    for category, cards in suggestions.items():
        print(f"\n{category.title()} ({len(cards)} cards):")
        for card in cards[:5]:
            print(f"- {card['card']['name']}")
        if len(cards) > 5:
            print(f"... and {len(cards)-5} more")
    
    # Option to view details
    if input("\nView full card details? (y/N): ").lower() == 'y':
        for category, cards in suggestions.items():
            print(f"\n=== {category.title()} ===")
            for card in cards:
                card_data = card['card']
                print(f"\n{card_data['name']}")
                print(f"Cost: {card_data.get('mana_cost', 'N/A')}")
                print(f"Type: {card_data.get('type_line', 'N/A')}")
                print(f"{card_data.get('oracle_text', '')}")
    
    # Save option
    if input("\nSave deck suggestions? (Y/n): ").lower() != 'n':
        if suggester:
            try:
                path = suggester.save_suggestions(suggestions)
                print(f"\nSaved to: {path}")
                print("You can find the deck in CSV, JSON, and Moxfield formats")
            except Exception as e:
                print(f"\nError saving deck: {str(e)}")
                print("Please check file permissions and disk space")
        else:
            print("Cannot save: no suggester provided")
            print("This can happen when viewing cached results")

def handle_deck_browsing() -> None:
    """Handle browsing of saved decks
    
    Shows list of previously built decks and allows:
    1. Viewing deck details
    2. Exporting to different formats
    3. Deleting saved decks
    """
    suggester = DeckSuggester()
    decks = suggester.list_saved_decks()
    
    print("\nSaved Decks")
    print("===========")
    
    if not decks:
        print("\nNo saved decks found")
        input("\nPress Enter to continue...")
        return
    
    print("\nAvailable Decks:")
    for i, deck in enumerate(decks, 1):
        print(f"\n{i}. {deck['file_name']}")
        print(f"   Colors: {'-'.join(deck['colors'])}")
        print(f"   Themes: {', '.join(deck['themes'])}")
    
    if input("\nView a deck? (Y/n): ").lower() != 'n':
        while True:
            try:
                choice = int(input("Enter deck number: "))
                if 1 <= choice <= len(decks):
                    deck = suggester.load_deck_suggestion(decks[choice-1]['file_name'])
                    show_deck_suggestions(deck['suggestions'], suggester)
                    break
                print("Invalid deck number")
            except ValueError:
                print("Please enter a number")
    
    input("\nPress Enter to continue...")

def main():
    while True:
        print_header()
        choice = show_main_menu()
        
        if choice == "1":
            handle_deck_building()
        elif choice == "2":
            handle_deck_browsing()
        elif choice == "3":
            handle_setup()
        elif choice == "4":
            print("\nExiting...")
            break
        else:
            print("\nInvalid choice")
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()