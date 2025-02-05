from pathlib import Path
from typing import Set, List, Dict
import json

from src.search import CardSearchEngine
from src.collectors.data_engine import DataEngine
from src.deckbuilding.engine import DeckbuildingEngine, ColorIdentity, DeckTheme
from src.deckbuilding.synergies import SynergyDetector
from src.deckbuilding.embeddings import CardEmbeddings
from src.deckbuilding.ml_synergies import SynergyModel

def print_header():
    print("\nMTG Deck Builder")
    print("================")

def show_main_menu() -> str:
    print("\nMain Menu:")
    print("1. Start New Deck")
    print("2. Analyze Existing Deck")
    print("3. Find Card Synergies")
    print("4. Browse Themes")
    print("5. Exit")
    return input("\nSelect an option (1-5): ")

def select_colors() -> Set[ColorIdentity]:
    """Let user select color identity"""
    print("\nSelect colors (space-separated):")
    print("W - White")
    print("U - Blue")
    print("B - Black")
    print("R - Red")
    print("G - Green")
    
    colors = set()
    while not colors:
        choice = input("\nColors: ").upper().split()
        colors = {ColorIdentity(c) for c in choice if c in "WUBRG"}
        if not colors:
            print("Please select at least one valid color")
    
    return colors

def browse_themes(engine: DeckbuildingEngine):
    """Browse available themes"""
    print("\nTheme Categories:")
    for i, category in enumerate(engine.theme_categories.keys(), 1):
        print(f"{i}. {category.title()}")
    
    choice = input("\nSelect category (or Enter for all): ")
    
    themes = []
    if choice.isdigit() and 1 <= int(choice) <= len(engine.theme_categories):
        category = list(engine.theme_categories.keys())[int(choice)-1]
        themes = engine.theme_categories[category]
    else:
        for category in engine.theme_categories.values():
            themes.extend(category)
    
    print("\nAvailable Themes:")
    for i, theme in enumerate(themes, 1):
        print(f"\n{i}. {theme.name}")
        print(f"   Colors: {', '.join(c.name for c in theme.colors)}")
        print(f"   Description: {theme.description}")
        print(f"   Key cards: {', '.join(theme.key_cards[:3])}...")
    
    return themes

def analyze_synergies(engine: DeckbuildingEngine, search: CardSearchEngine):
    """Find synergies between cards"""
    print("\nEnter card names (blank line to finish):")
    cards = []
    
    while True:
        name = input("> ").strip()
        if not name:
            break
            
        card = search.find_card(name)
        if card:
            cards.append(card)
            print(f"Added: {card.name}")
        else:
            print(f"Card not found: {name}")
    
    if len(cards) < 2:
        print("\nNeed at least 2 cards to analyze synergies")
        return
    
    # Use multiple synergy detection methods
    print("\nAnalyzing synergies...")
    
    # Pattern-based synergies
    detector = SynergyDetector()
    for i, card1 in enumerate(cards):
        for card2 in cards[i+1:]:
            print(f"\n=== {card1.name} + {card2.name} ===")
            
            # Check text-based synergies
            synergies1 = detector.find_synergies(card1.oracle_text)
            synergies2 = detector.find_synergies(card2.oracle_text)
            
            if synergies1 and synergies2:
                print("Pattern matches:")
                for s1 in synergies1:
                    for s2 in synergies2:
                        if s1['category'] == s2['category']:
                            print(f"- {s1['category'].title()}: {s1['type']} + {s2['type']}")
    
    # Embedding similarity
    embeddings = CardEmbeddings()
    embeddings.embed_cards([vars(c) for c in cards])
    
    print("\nSimilar cards by embedding:")
    for card in cards:
        similar = embeddings.find_similar_cards(vars(card), n=3)
        print(f"\n{card.name} is similar to:")
        for oracle_id, score in similar:
            if oracle_id != card.oracle_id:
                print(f"- {search.get_card_name(oracle_id)} ({score:.2f})")

def start_new_deck():
    """Start building a new deck"""
    # Initialize engines
    search = CardSearchEngine()
    data = DataEngine()
    engine = DeckbuildingEngine(search, data.themes)
    
    # Get color identity
    colors = select_colors()
    print(f"\nSelected colors: {', '.join(c.name for c in colors)}")
    
    # Show theme suggestions
    suggestions = engine.suggest_themes(colors)
    if suggestions:
        print("\nSuggested Themes:")
        for i, theme in enumerate(suggestions, 1):
            print(f"\n{i}. {theme.name}")
            print(f"   Description: {theme.description}")
            print(f"   Key cards: {', '.join(theme.key_cards[:3])}...")
        
        choice = input("\nSelect theme number (or Enter to skip): ")
        if choice.isdigit() and 1 <= int(choice) <= len(suggestions):
            theme = suggestions[int(choice)-1]
            
            # Find synergistic cards
            print("\nFinding synergistic cards...")
            synergies = engine.find_synergies(theme)
            
            print(f"\nCards that synergize with {theme.name}:")
            for card in synergies[:10]:  # Show top 10
                print(f"\n- {card['card'].name}")
                print(f"  {card['reason']}")

def main():
    print_header()
    
    while True:
        choice = show_main_menu()
        
        if choice == "1":
            start_new_deck()
        elif choice == "2":
            print("\nFeature coming soon!")
        elif choice == "3":
            search = CardSearchEngine()
            data = DataEngine()
            engine = DeckbuildingEngine(search, data.themes)
            analyze_synergies(engine, search)
        elif choice == "4":
            search = CardSearchEngine()
            data = DataEngine()
            engine = DeckbuildingEngine(search, data.themes)
            browse_themes(engine)
        elif choice == "5":
            print("\nExiting...")
            break
        else:
            print("\nInvalid choice")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()