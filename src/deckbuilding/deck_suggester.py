from pathlib import Path
import json
import torch
from typing import List, Dict, Optional
from collections import defaultdict
from tqdm import tqdm
import csv
from datetime import datetime

from .ml.semantic_analyzer import SemanticThemeAnalyzer
from .lib.theme_network import ThemeNetwork
from .lib.models import ColorIdentity
from .utils.exporters import export_to_csv, export_to_moxfield
from .utils.cache import CacheManager

class DeckSuggester:
    def __init__(self):
        self.analyzer = SemanticThemeAnalyzer()
        self.data_dir = Path("data")
        self.analysis_dir = self.data_dir / "analyzed_cards"
        self.analysis_dir.mkdir(parents=True, exist_ok=True)
        
        # Load data first
        self.load_data()
        
        # Initialize theme network (will use cache if available)
        self.theme_network = ThemeNetwork()
        
        # Only analyze if no cached data exists
        if not self.theme_network.themes:
            print("\nNo cached theme analysis found. Discovering themes...")
            self.theme_network.discover_themes(self.oracle_data)
    
    def load_data(self):
        """Load cached data and models"""
        with open("data/training/oracle_texts.json", 'r') as f:
            self.oracle_data = json.load(f)
        
        self.embeddings_data = torch.load("data/training/oracle_embeddings.pt")
        
        # Load cached analysis if exists
        self.analysis_cache = self._load_analysis_cache()
    
    def _load_analysis_cache(self) -> Dict:
        """Load cached card analysis results"""
        cache_file = self.analysis_dir / "card_analysis_cache.json"
        if cache_file.exists():
            print("Loading cached card analysis...")
            with open(cache_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_analysis_cache(self):
        """Save card analysis results"""
        cache_file = self.analysis_dir / "card_analysis_cache.json"
        with open(cache_file, 'w') as f:
            json.dump(self.analysis_cache, f, indent=2)
    
    def _get_cache_key(self, themes: List[str]) -> str:
        """Generate cache key for theme combination"""
        return "_".join(sorted(themes))
    
    def suggest_deck(self, 
                    colors: List[str], 
                    themes: List[str], 
                    max_suggestions: int = 40,
                    force_reanalyze: bool = False) -> Dict:
        """Suggest cards for a deck based on colors and themes"""
        # Expand themes with related concepts
        expanded_themes = []
        for theme in themes:
            theme_data = self.theme_network.get_expanded_theme(theme)
            if theme_data:
                expanded_themes.append(theme_data)
        
        # Get synergies between themes
        synergies = self.theme_network.suggest_synergies(themes)
        
        # Collect all relevant keywords and patterns
        all_keywords = set()
        all_patterns = set()
        for theme_data in expanded_themes:
            all_keywords.update(theme_data['all_keywords'])
            all_patterns.update(theme_data['all_patterns'])
        
        print("\nAnalyzing with expanded themes:")
        print(f"- Keywords: {', '.join(sorted(all_keywords))}")
        print(f"- Synergy patterns: {len(all_patterns)} patterns")
        
        if synergies:
            print("\nTheme Synergies:")
            for synergy in synergies:
                t1, t2 = synergy['themes']
                print(f"\n{t1.title()} + {t2.title()}:")
                if synergy['shared_keywords']:
                    print(f"- Shared keywords: {', '.join(synergy['shared_keywords'])}")
                if synergy['key_cards']:
                    print(f"- Key synergy cards: {', '.join(synergy['key_cards'])}")
        
        cache_key = self._get_cache_key(themes)
        
        # Check cache first
        if not force_reanalyze and cache_key in self.analysis_cache:
            print("Using cached analysis results...")
            cached_results = self.analysis_cache[cache_key]
            return self._filter_by_colors(cached_results, colors)
        
        # Perform new analysis
        suggestions = self._analyze_cards(colors, themes)
        
        # Cache the results
        self.analysis_cache[cache_key] = suggestions
        self._save_analysis_cache()
        
        # Save detailed results
        self._save_deck_suggestions(suggestions, colors, themes)
        
        return suggestions
    
    def _save_deck_suggestions(self, suggestions: Dict, colors: List[str], themes: List[str]):
        """Save deck suggestions in multiple formats"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        deck_name = f"{''.join(colors)}_{'-'.join(themes)}_{timestamp}"
        
        # Save as JSON with full card details
        json_file = self.analysis_dir / f"{deck_name}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'colors': colors,
                'themes': themes,
                'timestamp': timestamp,
                'suggestions': {
                    category: [{
                        'name': card_data['card']['name'],
                        'score': card_data['score'],
                        'mana_cost': card_data['card'].get('mana_cost', 'N/A'),
                        'type_line': card_data['card'].get('type_line', 'N/A'),
                        'oracle_text': card_data['card'].get('oracle_text', '')
                    } for card_data in cards]
                    for category, cards in suggestions.items()
                }
            }, f, indent=2)
        
        # Save other formats
        csv_file = self.analysis_dir / f"{deck_name}.csv"
        moxfield_file = self.analysis_dir / f"{deck_name}_moxfield.txt"
        
        self._export_to_csv(suggestions, csv_file)
        self._export_to_moxfield(suggestions, moxfield_file)
        
        print(f"\nResults saved to:")
        print(f"- Detailed JSON: {json_file}")
        print(f"- CSV format: {csv_file}")
        print(f"- Moxfield format: {moxfield_file}")
    
    def _export_to_csv(self, suggestions: Dict, file_path: Path):
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
    
    def _export_to_moxfield(self, suggestions: Dict, file_path: Path):
        """Export in Moxfield-compatible format"""
        with open(file_path, 'w', encoding='utf-8') as f:
            # Write commander first if exists
            if 'commander' in suggestions and suggestions['commander']:
                f.write("// Commander\n")
                commander = suggestions['commander'][0]['card']
                f.write(f"1 {commander['name']} (CMDR)\n")
                f.write(f"// {commander.get('oracle_text', '')}\n\n")
            
            # Write other categories
            for category, cards in suggestions.items():
                if category == 'commander':
                    continue
                
                f.write(f"\n// {category.title()} ({len(cards)} cards)\n")
                for card_data in cards:
                    card = card_data['card']
                    f.write(f"1 {card['name']}\n")
                    f.write(f"// {card.get('oracle_text', '')}\n")
    
    def load_deck_suggestion(self, file_name: str) -> Optional[Dict]:
        """Load a previously saved deck suggestion"""
        file_path = self.analysis_dir / file_name
        if not file_path.exists():
            print(f"No saved deck found: {file_name}")
            return None
            
        with open(file_path, 'r') as f:
            return json.load(f)
    
    def list_saved_decks(self) -> List[Dict]:
        """List all saved deck suggestions"""
        decks = []
        for file in self.analysis_dir.glob("*.json"):
            if file.name != "card_analysis_cache.json":
                with open(file, 'r') as f:
                    deck_data = json.load(f)
                    decks.append({
                        'file_name': file.name,
                        'colors': deck_data['colors'],
                        'themes': deck_data['themes'],
                        'timestamp': deck_data['timestamp']
                    })
        return sorted(decks, key=lambda x: x['timestamp'], reverse=True)

    def _analyze_cards(self, colors: List[str], themes: List[str], commander_text: str = None) -> Dict:
        """Analyze cards for themes and categorize them"""
        print(f"\nBuilding {'-'.join(colors)} deck with themes: {', '.join(themes)}")
        
        suggestions = defaultdict(list)
        color_ids = {ColorIdentity(c) for c in colors}
        theme_desc = commander_text if commander_text else " ".join(themes)
        
        # Card distribution targets
        category_limits = {
            'commander': 1,      # Commander
            'core': 25,         # Core theme pieces
            'support': 35,      # Support cards
            'utility': 25,      # Interaction/removal
            'lands': 14         # Non-basic lands that support theme
        }
        
        print("\nAnalyzing cards...")
        for oracle_id, card in tqdm(self.oracle_data["cards"].items()):
            # Check color identity
            card_colors = {ColorIdentity(c) for c in card['color_identity']}
            if not card_colors.issubset(color_ids):
                continue
            
            # Get theme fit
            card_text = f"{card['name']} {card['oracle_text']}"
            similarity, reasons = self.analyzer.analyze_card_theme_fit(
                card_text, theme_desc
            )
            
            if similarity > 0.5:  # Lower threshold for more suggestions
                category = self._categorize_card(card, reasons, similarity)
                suggestions[category].append({
                    'card': card,
                    'score': similarity,
                    'reasons': reasons
                })
        
        # Sort and limit each category
        final_suggestions = {}
        for category, limit in category_limits.items():
            if category in suggestions:
                cards = suggestions[category]
                cards.sort(key=lambda x: x['score'], reverse=True)
                final_suggestions[category] = cards[:limit]
        
        return final_suggestions

    def _categorize_card(self, card: Dict, reasons: List[str], score: float) -> str:
        """Categorize a card based on its characteristics"""
        type_line = card.get('type_line', '').lower()
        text = card.get('oracle_text', '').lower()
        
        # Commander candidates (legendary creatures in theme)
        if 'legendary' in type_line and 'creature' in type_line and score > 0.8:
            return 'commander'
        
        # Core theme pieces
        if score > 0.75 or any('key theme card' in r.lower() for r in reasons):
            return 'core'
        
        # Theme-supporting lands
        if 'land' in type_line and score > 0.6:
            return 'lands'
        
        # Support cards
        if any(word in text for word in ['whenever', 'trigger', 'each']):
            return 'support'
        
        # Utility cards (interaction/removal)
        if any(word in text for word in ['destroy', 'exile', 'counter', 'return']):
            return 'utility'
        
        return 'support'  # Default category

    def suggest_from_card(self, card: str) -> Dict:
        """
        Suggest a deck based on the given card.
        Analyzes the card's themes and suggests related cards for a deck.
        """
        print(f"Generating deck suggestions for card: {card}")
        suggestions = {}
        
        # Check if the card is found in the oracle data (case-insensitive match)
        matching_card = None
        for oracle_id, card_data in self.oracle_data['cards'].items():
            if card.lower() == card_data['name'].lower():
                matching_card = card_data
                break

        if matching_card:
            print(f"\nFound commander: {matching_card['name']}")
            # Add the card as commander
            suggestions['commander'] = [{
                'card': matching_card,
                'score': 1.0,
                'reasons': ["Commander card"]
            }]
            
            # Extract themes and patterns from the commander
            card_text = f"{matching_card['name']} {matching_card.get('oracle_text', '')}"
            similarity, reasons = self.analyzer.analyze_card_theme_fit(card_text, card_text)
            
            # Get color identity for filtering
            colors = matching_card.get('color_identity', ['C'])
            
            print("\nAnalyzing commander's themes...")
            print(f"Colors: {', '.join(colors)}")
            print("Themes found:")
            for reason in reasons:
                print(f"- {reason}")
            
            # Find related cards based on commander's themes
            related_suggestions = self._analyze_cards(
                colors=colors,
                themes=[matching_card['name']],  # Use card name as theme
                commander_text=card_text  # Pass commander text for similarity matching
            )
            
            # Add related cards to suggestions
            for category in ['core', 'support', 'utility', 'lands']:
                suggestions[category] = related_suggestions.get(category, [])
        else:
            print(f"Card not found: {card}")
            # Return empty categories
            suggestions['commander'] = []
            suggestions['core'] = []
            suggestions['support'] = []
            suggestions['utility'] = []
            suggestions['lands'] = []
        return suggestions

    def save_suggestions(self, suggestions: Dict) -> Path:
        """
        Public method to save deck suggestions.
        Returns the path where suggestions were saved.
        """
        # Use placeholder values if we don't have colors/themes (e.g., for card-based suggestions)
        colors = ['C']  # C for colorless/unknown
        themes = ['custom']
        
        # If this is a commander deck, try to get colors from the commander
        if 'commander' in suggestions and suggestions['commander']:
            commander = suggestions['commander'][0]['card']
            if 'color_identity' in commander:
                colors = commander['color_identity']
        
        self._save_deck_suggestions(suggestions, colors, themes)
        return self.analysis_dir

def main():
    suggester = DeckSuggester()
    
    # List existing decks
    print("\nPreviously analyzed decks:")
    for deck in suggester.list_saved_decks():
        print(f"- {deck['file_name']}: {'-'.join(deck['colors'])} {', '.join(deck['themes'])}")
    
    # Example: Golgari Dredge deck
    colors = ['B', 'G']
    themes = ['dredge', 'graveyard', 'sacrifice']
    
    suggestions = suggester.suggest_deck(colors, themes)

if __name__ == "__main__":
    main() 