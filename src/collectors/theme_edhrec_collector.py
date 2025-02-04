from pathlib import Path
from datetime import datetime
import requests
import json
from bs4 import BeautifulSoup

class EDHRECThemeCollector:
    """Collects theme data from EDHREC"""
    
    EDHREC_THEMES_URL = "https://edhrec.com/tags/themes"
    
    def __init__(self, cache_dir: str = "cache/themes/edhrec", data_dir: str = "data/themes/edhrec"):
        # Cache directory for raw downloads
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Data directory for processed data
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache files (raw data)
        self.raw_themes_file = self.cache_dir / "themes_raw.json"
        self.cache_metadata_file = self.cache_dir / "metadata.json"
        
        # Data files (processed data)
        self.themes_file = self.data_dir / "themes.json"
        self.metadata_file = self.data_dir / "metadata.json"
        
        # Initialize data structure
        self.themes = {}
        self.load_themes()
    
    def load_themes(self):
        """Load or initialize themes"""
        if self.themes_file.exists():
            with open(self.themes_file, 'r') as f:
                self.themes = json.load(f)
    
    def save_themes(self):
        """Save current themes data"""
        with open(self.themes_file, 'w') as f:
            json.dump(self.themes, f, indent=2)
        
        # Update metadata
        with open(self.metadata_file, 'w') as f:
            json.dump({
                'last_updated': datetime.now().isoformat(),
                'theme_count': sum(len(themes) for themes in self.themes.values())
            }, f, indent=2)
    
    def update_themes(self):
        """Update theme data"""
        theme_data = self.scrape_current_themes()
        if theme_data:
            self.themes = theme_data
            self.save_themes()
            print(f"Saved {sum(len(themes) for themes in theme_data.values())} themes to {self.themes_file}")
        else:
            print("No theme data collected")
    
    def scrape_current_themes(self) -> dict:
        """Extract theme data from EDHREC"""
        print("Fetching themes from EDHREC...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            response = requests.get(self.EDHREC_THEMES_URL, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            themes = {}
            
            # Look for cards with the new class name pattern
            cards = soup.find_all('div', class_=lambda x: x and 'Card_container' in x)
            
            if not cards:
                print("No theme cards found. Website structure might have changed.")
                print("Saving HTML for inspection...")
                with open(self.cache_dir / "last_response.html", 'w', encoding='utf-8') as f:
                    f.write(response.text)
                return {}
            
            print(f"Found {len(cards)} theme cards")
            current_category = "Uncategorized"
            themes[current_category] = {}
            
            for card in cards:
                try:
                    # Find the name wrapper and extract the name
                    name_wrapper = card.find('div', class_=lambda x: x and 'Card_nameWrapper' in x)
                    if not name_wrapper:
                        continue
                        
                    name = name_wrapper.get_text().strip()
                    
                    # Find the label for deck count
                    label = card.find('div', class_=lambda x: x and 'CardLabel_label' in x)
                    deck_count = 0
                    if label:
                        # Extract number from text like "1,234 decks"
                        count_text = label.get_text().strip()
                        if 'decks' in count_text.lower():
                            deck_count = int(count_text.split()[0].replace(',', ''))
                    
                    # Get color identity from data attribute or class
                    colors = []
                    color_div = card.find('div', {'data-colors': True})
                    if color_div:
                        colors = [c.lower() for c in color_div['data-colors'].split()]
                    
                    themes[current_category][name] = {
                        'colors': colors,
                        'deck_count': deck_count
                    }
                    print(f"Found theme: {name} ({deck_count} decks) - Colors: {colors}")
                    
                except Exception as e:
                    print(f"Error processing theme card: {e}")
                    continue
            
            # Remove empty categories
            themes = {k: v for k, v in themes.items() if v}
            
            if not themes:
                print("No themes were successfully processed")
                return {}
            
            # Save raw data for debugging
            with open(self.cache_dir / "raw_themes.json", 'w', encoding='utf-8') as f:
                json.dump(themes, f, indent=2)
            
            return themes
            
        except Exception as e:
            print(f"Error collecting themes: {e}")
            if 'response' in locals():
                print(f"Response status: {response.status_code}")
                print(f"Response headers: {response.headers}")
            return {}

if __name__ == "__main__":
    collector = EDHRECThemeCollector()
    collector.update_themes() 