from enum import Enum
from pathlib import Path
import csv
from typing import Dict, List
import json
from datetime import datetime

class ExportFormat(Enum):
    """Supported export formats"""
    JSON = "json"
    CSV = "csv"
    MOXFIELD = "txt"

def export_to_json(suggestions: Dict, file_path: Path):
    """Export suggestions to JSON format with metadata"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'suggestions': suggestions
        }, f, indent=2)

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
        for category, cards in suggestions.items():
            for card_data in cards:
                card = card_data['card']
                f.write(f"1 {card['name']}\n")

def export_deck(
    suggestions: Dict[str, List[Dict]], 
    file_path: Path,
    format: ExportFormat
) -> None:
    """Export deck in specified format
    
    Args:
        suggestions: Deck suggestions dict
        file_path: Base path for export (without extension)
        format: Desired export format (from ExportFormat enum)
    
    The function will automatically append the correct extension
    based on the chosen format.
    
    Raises:
        OSError: If there are file permission or disk space issues
        ValueError: If the suggestions dict has an invalid structure
    """
    # Validate input
    if not isinstance(suggestions, dict):
        raise ValueError("suggestions must be a dictionary")
    if not isinstance(file_path, Path):
        raise ValueError("file_path must be a Path object")
    if not isinstance(format, ExportFormat):
        raise ValueError("format must be an ExportFormat enum value")

    try:
        if format == ExportFormat.JSON:
            export_to_json(suggestions, file_path.with_suffix('.json'))
        elif format == ExportFormat.CSV:
            export_to_csv(suggestions, file_path.with_suffix('.csv'))
        elif format == ExportFormat.MOXFIELD:
            export_to_moxfield(suggestions, file_path.with_suffix('.txt'))
    except OSError as e:
        raise OSError(f"Error exporting deck: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error processing deck data: {str(e)}") 