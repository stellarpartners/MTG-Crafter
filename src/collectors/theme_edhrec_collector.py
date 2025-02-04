import pandas as pd
from datetime import datetime
from pathlib import Path
import requests
import re
import json
from time import sleep
from bs4 import BeautifulSoup

class ThemeEDHRECCollector:
    """Collects and manages theme data from EDHREC"""
    
    EDHREC_API_URL = "https://api2.edhrec.com/v1/graphql"
    EDHREC_THEMES_URL = "https://edhrec.com/tags/themes"
    
    def __init__(self, data_dir: str = "sources"):
        self.data_dir = Path(data_dir)
        self.raw_dir = Path("data/raw")
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.themes_file = self.data_dir / "themes-EDHREC.csv"
        self.debug_file = self.raw_dir / "debug_page.html"
        self.raw_themes_file = self.raw_dir / "themes_raw.json"
        
    def scrape_current_themes(self) -> dict:
        """Extract theme data from EDHREC's embedded JSON"""
        print("Fetching themes from EDHREC...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
        
        try:
            response = requests.get(self.EDHREC_THEMES_URL, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Save raw HTML for debugging
            with open(self.debug_file, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            # Extract JSON data
            json_start = response.text.find('type="application/json">')
            json_text = response.text[json_start + 24:]  # Skip the prefix
            json_end = json_text.find('</script>')
            json_data = json.loads(json_text[:json_end])
            
            # Process theme data
            theme_data = {}
            theme_colors = {}
            theme_categories = {}  # Track which category each theme belongs to
            
            # Extract from related_info
            for category in json_data['props']['pageProps']['data']['related_info']:
                category_name = category['header']
                print(f"\nProcessing category: {category_name}")
                
                for item in category['items']:
                    name = item['textLeft']
                    count = item['count']
                    colors = item['colors']
                    url = item['url']
                    
                    theme_data[name] = count
                    theme_colors[name] = colors
                    theme_categories[name] = category_name
                    print(f"Found theme: {name} ({count} decks) - Colors: {colors}")
            
            # Save complete theme data
            with open(self.raw_themes_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'themes': theme_data,
                    'colors': theme_colors,
                    'categories': theme_categories,
                    'collected_at': datetime.now().isoformat()
                }, f, indent=2)
            
            print(f"\nSummary:")
            print(f"Total themes found: {len(theme_data)}")
            print("\nThemes by category:")
            category_counts = {}
            for theme, category in theme_categories.items():
                category_counts[category] = category_counts.get(category, 0) + 1
            for category, count in category_counts.items():
                print(f"- {category}: {count} themes")
            
            return theme_data
            
        except Exception as e:
            print(f"Error processing themes: {e}")
            print(f"Response text: {response.text[:500] if 'response' in locals() else 'No response'}")
            return {}
    
    def update_themes(self):
        """Scrape current data and add as new column"""
        # Get current theme data
        new_data = self.scrape_current_themes()
        
        # Add as new column
        self.add_new_date_column(new_data)
        print("Theme data updated successfully")
    
    def load_themes(self) -> pd.DataFrame:
        """Load theme data into a pandas DataFrame"""
        return pd.read_csv(self.themes_file)
    
    def add_new_date_column(self, new_data: dict):
        """Add a new date column with updated counts for a specific date"""
        # Get the last date from existing columns
        df = self.load_themes()
        date_columns = [col for col in df.columns if col != 'THEME']
        last_date = datetime.strptime(date_columns[-1], '%Y-%m-%d')
        
        # Calculate next collection date (1 year after last collection)
        next_date = (last_date.replace(year=last_date.year + 1)).strftime('%Y-%m-%d')
        
        # Read existing data
        df = self.load_themes()
        
        # Add new column with the next date
        df[next_date] = df['THEME'].map(new_data).fillna(df[df.columns[-1]])
        
        # Save updated data
        df.to_csv(self.themes_file, index=False)
        
    def get_theme_history(self, theme_name: str) -> dict:
        """Get historical data for a specific theme"""
        df = self.load_themes()
        if theme_name not in df['THEME'].values:
            return {}
            
        theme_row = df[df['THEME'] == theme_name].iloc[0]
        return {col: theme_row[col] for col in df.columns if col != 'THEME'}
    
    def get_trending_themes(self, days: int = 30) -> pd.DataFrame:
        """Get themes with the biggest changes in the last N days"""
        df = self.load_themes()
        date_columns = [col for col in df.columns if col != 'THEME']
        
        if len(date_columns) < 2:
            return pd.DataFrame()
            
        latest = date_columns[-1]
        comparison = date_columns[-min(len(date_columns), days)]
        
        df['change'] = df[latest] - df[comparison]
        df['change_pct'] = (df['change'] / df[comparison] * 100).round(2)
        
        return df.sort_values('change_pct', ascending=False)[['THEME', 'change', 'change_pct']]

if __name__ == "__main__":
    collector = ThemeEDHRECCollector()
    
    print("EDHREC Theme Collector")
    print("---------------------")
    
    # Scrape and update
    collector.update_themes()
    
    # Show some trending themes
    print("\nTop Trending Themes:")
    trending = collector.get_trending_themes(days=365)  # Compare year over year
    print(trending.head(10)) 