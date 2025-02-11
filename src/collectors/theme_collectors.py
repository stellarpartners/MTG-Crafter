"""Collection of theme collectors from different sources"""

from pathlib import Path
import json
from typing import Dict, List, Optional
from datetime import datetime
import sys
from os.path import dirname, abspath

# Add src to Python path for imports
root_dir = dirname(dirname(dirname(abspath(__file__))))
sys.path.append(root_dir)

# Use absolute imports
from src.collectors.theme_edhrec_collector import EDHRECThemeCollector

class ThemeCollector:
    """Main collector for theme data from various sources"""
    
    def __init__(self, cache_dir: str = "cache/themes", data_dir: str = "data/themes"):
        self.cache_dir = Path(cache_dir)
        self.data_dir = Path(data_dir)
        
        # Create directories
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize sub-collectors
        self.edhrec = EDHRECThemeCollector(
            cache_dir=str(self.cache_dir / "edhrec")
        )
        # Future collectors can be added here:
        # self.mtggoldfish = ThemeMTGGoldfishCollector()
        # self.archidekt = ThemeArchidektCollector()
    
    def update_all(self):
        """Update themes from all sources"""
        print("Updating EDHREC themes...")
        self.edhrec.update_themes()
        # Add other collectors as they become available

    def update(self):
        """Public update method"""
        return self.update_all()

if __name__ == "__main__":
    collector = ThemeCollector()
    collector.update_all() 