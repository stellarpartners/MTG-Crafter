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
            
            # Process theme sections
            for section in soup.find_all('section', class_='container'):
                category = section.find('h2')
                if not category:
                    continue
                    
                category_name = category.text.strip()
                themes[category_name] = {}
                
                # Process themes in this category
                for theme in section.find_all('div', class_='card'):
                    name = theme.find('h3').text.strip()
                    deck_count = int(theme.find('span', class_='deck-count').text.strip())
                    colors = [c.lower() for c in theme.get('data-colors', '').split()]
                    
                    themes[category_name][name] = {
                        'colors': colors,
                        'deck_count': deck_count
                    }
                    print(f"Found theme: {name} ({deck_count} decks) - Colors: {colors}")
            
            return themes
            
        except Exception as e:
            print(f"Error collecting themes: {e}")
            return {}

if __name__ == "__main__":
    collector = EDHRECThemeCollector()
    collector.update_themes() 