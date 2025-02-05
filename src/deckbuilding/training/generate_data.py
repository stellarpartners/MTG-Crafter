from pathlib import Path
import json
from typing import List, Dict
from tqdm import tqdm

def generate_training_examples():
    """Generate training examples from known synergies"""
    
    # Known theme examples
    theme_examples = {
        "counters": {
            "positive": [
                "Hardened Scales",  # Amplifies +1/+1 counters
                "Vorinclex, Monstrous Raider",  # Doubles counters
                "Evolution Sage",  # Proliferate on landfall
                "Winding Constrictor",  # Amplifies counters
            ],
            "negative": [
                "Lightning Bolt",  # Just damage
                "Counterspell",  # Just control
                "Dark Ritual",  # Just mana
            ]
        },
        "graveyard": {
            "positive": [
                "Golgari Grave-Troll",  # Dredge
                "Animate Dead",  # Reanimation
                "Life from the Loam",  # Recursion
                "Stitcher's Supplier",  # Mill
            ],
            "negative": [
                "Giant Growth",  # Combat trick
                "Birds of Paradise",  # Mana only
                "Wrath of God",  # Board wipe only
            ]
        },
        # Add more themes...
    }
    
    # Load oracle texts
    with open("data/training/oracle_texts.json", 'r') as f:
        oracle_data = json.load(f)
    
    # Generate examples
    examples = []
    
    for theme, cards in theme_examples.items():
        # Positive examples
        for card_name in cards["positive"]:
            card = find_card_by_name(oracle_data["cards"], card_name)
            if card:
                examples.append({
                    "card_text": f"{card['name']} {card['oracle_text']}",
                    "theme": theme,
                    "fits": 1
                })
        
        # Negative examples
        for card_name in cards["negative"]:
            card = find_card_by_name(oracle_data["cards"], card_name)
            if card:
                examples.append({
                    "card_text": f"{card['name']} {card['oracle_text']}",
                    "theme": theme,
                    "fits": 0
                })
    
    # Save examples
    output_file = Path("data/training/theme_examples.json")
    with open(output_file, 'w') as f:
        json.dump(examples, f, indent=2)
    
    print(f"Generated {len(examples)} training examples")
    return examples

def find_card_by_name(cards: Dict, name: str) -> Dict:
    """Find card data by name"""
    for oracle_id, card in cards.items():
        if card["name"].lower() == name.lower():
            return card
    return None

if __name__ == "__main__":
    generate_training_examples() 