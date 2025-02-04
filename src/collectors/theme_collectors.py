"""Collection of theme collectors from different sources"""

from .theme_edhrec_collector import ThemeEDHRECCollector

class ThemeCollector:
    """Manages theme collection from multiple sources"""
    
    def __init__(self):
        self.edhrec = ThemeEDHRECCollector()
        # Future collectors can be added here:
        # self.mtggoldfish = ThemeMTGGoldfishCollector()
        # self.archidekt = ThemeArchidektCollector()
    
    def update_all(self):
        """Update themes from all sources"""
        print("Updating EDHREC themes...")
        self.edhrec.update_themes()
        # Add other collectors as they become available 