import json
from pathlib import Path
from typing import Dict, List
import requests
import time

class BanlistCollector:
    """Collects ban list data from various sources"""
    
    def __init__(self, cache_dir: str = "cache/banlists", data_dir: str = "data/banlists"):
        # Cache directory for raw downloads
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Data directory for processed data
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache files (raw data)
        self.raw_banlists = self.cache_dir / "raw_banlists.json"
        self.cache_metadata = self.cache_dir / "metadata.json"
        
        # Data files (processed data)
        self.banlists_file = self.data_dir / "banlists.json"
        self.metadata_file = self.data_dir / "metadata.json"
        
    def fetch_banned_cards(self) -> Dict[str, List[Dict]]:
        """Fetch banned cards for all formats from Scryfall"""
        formats = [
            'standard', 'modern', 'legacy', 'vintage', 
            'commander', 'pioneer', 'pauper', 'brawl'
        ]
        
        banned_cards = {}
        
        for format_name in formats:
            print(f"\nFetching banned cards for {format_name}...")
            query = f"banned:{format_name}"
            if format_name == 'vintage':
                query = "banned:vintage or restricted:vintage"
            
            url = "https://api.scryfall.com/cards/search"
            params = {'q': query, 'order': 'name'}
            
            try:
                response = requests.get(url, params=params)
                
                # Handle case where format has no banned cards
                if response.status_code == 404:
                    print(f"No banned cards found for {format_name}")
                    banned_cards[format_name] = []
                    continue
                    
                response.raise_for_status()
                data = response.json()
                
                banned_list = []
                # Process first page
                for card in data.get('data', []):
                    banned_info = {
                        'name': card['name'],
                        'id': card['id'],
                        'status': 'restricted' if format_name == 'vintage' and 
                                card.get('legalities', {}).get('vintage') == 'restricted' 
                                else 'banned'
                    }
                    banned_list.append(banned_info)
                
                # Handle pagination
                while data.get('has_more', False):
                    time.sleep(0.1)  # Rate limiting
                    response = requests.get(data['next_page'])
                    response.raise_for_status()
                    data = response.json()
                    
                    for card in data.get('data', []):
                        banned_info = {
                            'name': card['name'],
                            'id': card['id'],
                            'status': 'restricted' if format_name == 'vintage' and 
                                    card.get('legalities', {}).get('vintage') == 'restricted' 
                                    else 'banned'
                        }
                        banned_list.append(banned_info)
                
                banned_cards[format_name] = banned_list
                print(f"Found {len(banned_list)} banned/restricted cards in {format_name}")
                
            except requests.exceptions.RequestException as e:
                if hasattr(e.response, 'status_code') and e.response.status_code == 404:
                    print(f"No banned cards found for {format_name}")
                    banned_cards[format_name] = []
                else:
                    print(f"Error fetching banned cards for {format_name}: {e}")
                    banned_cards[format_name] = []
        
        # Save raw banned data
        output_file = self.processed_dir / "banned_cards.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(banned_cards, f, indent=2)
            
        return banned_cards
    
    def generate_banlist_markdown(self, banned_cards: Dict[str, List[Dict]]):
        """Generate a markdown file with banned cards"""
        output = "# Magic: The Gathering Banned & Restricted Lists\n\n"
        output += f"Last updated: {time.strftime('%Y-%m-%d')}\n\n"
        
        for format_name, cards in banned_cards.items():
            output += f"## {format_name.title()}\n\n"
            
            if format_name == 'vintage':
                # Separate banned and restricted for Vintage
                banned = [card for card in cards if card['status'] == 'banned']
                restricted = [card for card in cards if card['status'] == 'restricted']
                
                output += "### Banned\n\n"
                for card in banned:
                    output += f"- {card['name']}\n"
                    
                output += "\n### Restricted\n\n"
                for card in restricted:
                    output += f"- {card['name']}\n"
            else:
                for card in cards:
                    output += f"- {card['name']}\n"
            
            output += "\n"
        
        # Save markdown file
        output_file = Path("docs/rules/current_banlists.md")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output)

if __name__ == "__main__":
    collector = BanlistCollector()
    
    print("Fetching banned cards from Scryfall...")
    banned_cards = collector.fetch_banned_cards()
    
    print("\nGenerating markdown documentation...")
    collector.generate_banlist_markdown(banned_cards)
    
    print("\nDone! Check docs/rules/current_banlists.md for the updated ban lists.") 