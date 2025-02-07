"""
Pattern Learning Pipeline

This script orchestrates the collection and analysis of deck data from various sources.
It provides a step-by-step process to:
1. Collect deck URLs from supported sources
2. Scrape deck data
3. Process and analyze the collected data
4. Generate pattern insights
"""

import sys
from pathlib import Path
from typing import List, Dict
import time
import json

# Add src directory to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

try:
    from src.deckbuilding.pattern_learning.magicgg_collector import DecklistCollector as MagicGGCollector
    from src.deckbuilding.pattern_learning.magicgg_scraper import process_all_urls as process_magicgg_urls
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please ensure you're running the script from the project root directory")
    print(f"Current sys.path: {sys.path}")
    sys.exit(1)

def show_menu() -> str:
    """Display menu and get user choice"""
    print("\nMTG Crafter - Pattern Learning Pipeline")
    print("=======================================")
    print("1. Collect URLs from all sources")
    print("2. Scrape deck data")
    print("3. Analyze patterns")
    print("4. Show statistics")
    print("5. Exit")
    return input("\nSelect an option (1-5): ").strip()

def collect_urls():
    """Step 1: Collect URLs from all supported sources"""
    print("\nCollecting URLs from supported sources...")
    
    # Magic.gg collection
    print("\n1. Magic.gg decklists:")
    collector = MagicGGCollector()
    collector.update_decklists()
    
    # Future sources will be added here
    # print("\n2. Some other source:")
    # collector = OtherSourceCollector()
    # collector.update_decklists()

def scrape_decks():
    """Step 2: Scrape deck data from collected URLs"""
    print("\nScraping deck data...")
    
    # Magic.gg scraping
    print("\n1. Processing Magic.gg URLs:")
    process_magicgg_urls()
    
    # Future sources will be added here
    # print("\n2. Processing other source URLs:")
    # process_other_source_urls()

def analyze_patterns():
    """Step 3: Analyze the collected deck data for patterns"""
    print("\nAnalyzing patterns in collected data...")
    print("(This feature is coming soon)")
    # TODO: Implement pattern analysis

def show_stats():
    """Step 4: Display statistics about collected data"""
    print("\nCollection Statistics")
    print("====================")
    
    # Magic.gg stats
    magicgg_dir = Path("cache/pattern_learning/magicgg")
    urls_file = magicgg_dir / "decklist_urls.csv"
    decks_dir = magicgg_dir / "decks"
    
    url_count = sum(1 for _ in open(urls_file)) - 1 if urls_file.exists() else 0
    deck_count = len(list(decks_dir.glob("*.json"))) if decks_dir.exists() else 0
    
    print("\nMagic.gg:")
    print(f"- Collected URLs: {url_count}")
    print(f"- Scraped Decks: {deck_count}")
    
    # Future sources will add their stats here

def main():
    """Main program loop"""
    while True:
        choice = show_menu()
        
        if choice == "1":
            collect_urls()
        elif choice == "2":
            scrape_decks()
        elif choice == "3":
            analyze_patterns()
        elif choice == "4":
            show_stats()
        elif choice == "5":
            print("\nExiting Pattern Learning Pipeline...")
            break
        else:
            print("\nInvalid choice. Please select 1-5.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main() 