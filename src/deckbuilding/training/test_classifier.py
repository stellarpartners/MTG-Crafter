from .semantic_analyzer import SemanticThemeAnalyzer
from .generate_training_data import find_card_by_name
from pathlib import Path
import json

def test_classifier():
    """Test the theme classifier on some examples"""
    # Load a trained classifier
    analyzer = SemanticThemeAnalyzer()
    
    # Test cards
    test_cards = [
        "Doubling Season",
        "Grave Titan",
        "Lightning Bolt",
        "Birds of Paradise"
    ]
    
    # Load oracle texts
    with open("data/training/oracle_texts.json", 'r') as f:
        oracle_data = json.load(f)
    
    print("\nTesting theme classification:")
    for card_name in test_cards:
        card = find_card_by_name(oracle_data["cards"], card_name)
        if not card:
            continue
            
        print(f"\n=== {card_name} ===")
        card_text = f"{card['name']} {card['oracle_text']}"
        
        # Test against each theme
        for theme in ["counters", "graveyard"]:
            similarity, reasons = analyzer.analyze_card_theme_fit(
                card_text, 
                f"{theme} theme"
            )
            print(f"\n{theme.title()} theme fit: {similarity:.2f}")
            if reasons:
                print("Reasons:")
                for reason in reasons:
                    print(f"- {reason}")

if __name__ == "__main__":
    test_classifier() 