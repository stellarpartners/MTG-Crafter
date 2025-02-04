"""Collection of theme collectors from different sources"""

from pathlib import Path
from datetime import datetime
import sys
from os.path import dirname, abspath

# Add src to Python path for imports
root_dir = dirname(dirname(dirname(abspath(__file__))))
sys.path.append(root_dir)

# Use absolute imports
from src.collectors.theme_edhrec_collector import EDHRECThemeCollector

class ThemeCollector:
    """Manages all theme collectors"""
    
    def __init__(self, cache_dir: str = "cache/themes", data_dir: str = "data/themes"):
        # Set up directories
        self.cache_dir = Path(cache_dir)
        self.data_dir = Path(data_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize collectors with their specific directories
        self.edhrec = EDHRECThemeCollector(
            cache_dir=str(self.cache_dir / "edhrec"),
            data_dir=str(self.data_dir / "edhrec")
        )
        # Future collectors can be added here:
        # self.mtggoldfish = ThemeMTGGoldfishCollector()
        # self.archidekt = ThemeArchidektCollector()
    
    def update_all(self):
        """Update themes from all sources"""
        print("Updating EDHREC themes...")
        self.edhrec.update_themes()
        # Add other collectors as they become available

if __name__ == "__main__":
    collector = ThemeCollector()
    collector.update_all() 