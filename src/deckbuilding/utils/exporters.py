from pathlib import Path
import csv
from typing import Dict

def export_to_csv(suggestions: Dict, file_path: Path):
    """Export suggestions to CSV format"""
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Category', 'Name', 'Score', 'Cost', 'Type', 'Oracle Text'])
        
        for category, cards in suggestions.items():
            for card_data in cards:
                card = card_data['card']
                writer.writerow([
                    category,
                    card['name'],
                    f"{card_data['score']:.2f}",
                    card.get('mana_cost', 'N/A'),
                    card.get('type_line', 'N/A'),
                    card.get('oracle_text', '')
                ])

def export_to_moxfield(suggestions: Dict, file_path: Path):
    """Export in Moxfield-compatible format"""
    with open(file_path, 'w', encoding='utf-8') as f:
        if 'commander' in suggestions and suggestions['commander']:
            f.write("// Commander\n")
            commander = suggestions['commander'][0]['card']
            f.write(f"1 {commander['name']} (CMDR)\n")
            f.write(f"// {commander.get('oracle_text', '')}\n\n")
        
        for category, cards in suggestions.items():
            if category == 'commander':
                continue
            
            f.write(f"\n// {category.title()} ({len(cards)} cards)\n")
            for card_data in cards:
                card = card_data['card']
                f.write(f"1 {card['name']}\n")
                f.write(f"// {card.get('oracle_text', '')}\n") 