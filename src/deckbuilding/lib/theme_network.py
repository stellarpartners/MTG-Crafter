from typing import Dict, List, Set, Tuple
from dataclasses import dataclass
from .theme_learner import ThemeLearner, DiscoveredTheme
import json
from pathlib import Path

@dataclass
class ThemeNode:
    name: str
    description: str
    keywords: List[str]
    related_themes: List[str]
    synergy_patterns: List[str]
    key_cards: List[str]

class ThemeNetwork:
    def __init__(self):
        self.theme_learner = ThemeLearner()
        self.themes = {}
        self.relationships = []
        self.cache_dir = Path("data/themes")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Try to load cached themes first
        if self._load_cached_analysis():
            print("Loaded cached theme analysis")
        else:
            print("No cached theme analysis found")

    def _get_cache_files(self) -> Tuple[Path, Path]:
        """Get paths to cache files"""
        return (
            self.cache_dir / "discovered_themes.json",
            self.cache_dir / "theme_relationships.json"
        )

    def _load_cached_analysis(self) -> bool:
        """Load cached theme analysis if available"""
        themes_file, relationships_file = self._get_cache_files()
        
        if not themes_file.exists() or not relationships_file.exists():
            return False
        
        try:
            # Load themes
            with open(themes_file, 'r', encoding='utf-8') as f:
                themes_data = json.load(f)
                self.themes = {
                    name: DiscoveredTheme(**data)
                    for name, data in themes_data.items()
                }
            
            # Load relationships
            with open(relationships_file, 'r', encoding='utf-8') as f:
                self.relationships = json.load(f)
            
            return True
        except Exception as e:
            print(f"Error loading cached analysis: {e}")
            return False

    def _save_analysis_cache(self):
        """Save current theme analysis to cache"""
        themes_file, relationships_file = self._get_cache_files()
        
        # Save themes
        with open(themes_file, 'w', encoding='utf-8') as f:
            # Convert DiscoveredTheme objects to dict
            themes_data = {
                name: {
                    'name': theme.name,
                    'description': theme.description,
                    'keywords': theme.keywords,
                    'key_cards': theme.key_cards,
                    'related_patterns': theme.related_patterns,
                    'similarity_score': theme.similarity_score
                }
                for name, theme in self.themes.items()
            }
            json.dump(themes_data, f, indent=2)
        
        # Save relationships
        with open(relationships_file, 'w', encoding='utf-8') as f:
            json.dump(self.relationships, f, indent=2)

    def discover_themes(self, oracle_data: Dict, force_reanalyze: bool = False):
        """Discover themes from card data"""
        if not force_reanalyze and self.themes:
            print("Using cached theme analysis")
            self._print_theme_summary()
            return
        
        print("Discovering themes from card data...")
        self.themes = self.theme_learner.discover_themes(oracle_data)
        self.relationships = self.theme_learner.find_theme_relationships(self.themes)
        
        # Save analysis to cache
        self._save_analysis_cache()
        
        self._print_theme_summary()

    def _print_theme_summary(self):
        """Print summary of discovered themes"""
        print("\nDiscovered Themes:")
        for name, theme in self.themes.items():
            print(f"\n{name}:")
            print(f"Description: {theme.description}")
            print(f"Key cards: {', '.join(theme.key_cards)}")
            print(f"Keywords: {', '.join(theme.keywords[:5])}...")
        
        print("\nTheme Relationships:")
        for theme1, theme2, score in self.relationships[:10]:
            print(f"{theme1} <-> {theme2}: {score:.2f}")
    
    def get_expanded_theme(self, theme_name: str) -> Dict:
        """Get a theme and all its related concepts"""
        if theme_name not in self.themes:
            return None
            
        theme = self.themes[theme_name]
        
        # Get related themes
        related_themes = [
            self.themes[related]
            for related in theme.related_themes
            if related in self.themes
        ]
        
        return {
            'main_theme': theme,
            'related_themes': related_themes,
            'all_keywords': self._gather_keywords(theme, related_themes),
            'all_patterns': self._gather_patterns(theme, related_themes)
        }
    
    def _gather_keywords(self, theme: ThemeNode, related_themes: List[ThemeNode]) -> Set[str]:
        """Gather all keywords from a theme and its related themes"""
        keywords = set(theme.keywords)
        for related in related_themes:
            keywords.update(related.keywords)
        return keywords
    
    def _gather_patterns(self, theme: ThemeNode, related_themes: List[ThemeNode]) -> Set[str]:
        """Gather all synergy patterns from a theme and its related themes"""
        patterns = set(theme.synergy_patterns)
        for related in related_themes:
            patterns.update(related.synergy_patterns)
        return patterns

    def suggest_synergies(self, themes: List[str]) -> List[Dict]:
        """Suggest synergistic combinations between themes"""
        synergies = []
        
        for i, theme1 in enumerate(themes):
            for theme2 in themes[i+1:]:
                if theme1 in self.themes and theme2 in self.themes:
                    t1 = self.themes[theme1]
                    t2 = self.themes[theme2]
                    
                    # Check for direct relationships
                    if theme2 in t1.related_themes or theme1 in t2.related_themes:
                        # Find shared keywords and patterns
                        shared_keywords = set(t1.keywords) & set(t2.keywords)
                        shared_patterns = set(t1.synergy_patterns) & set(t2.synergy_patterns)
                        
                        synergies.append({
                            'themes': (theme1, theme2),
                            'shared_keywords': list(shared_keywords),
                            'shared_patterns': list(shared_patterns),
                            'key_cards': self._find_synergy_cards(t1, t2)
                        })
        
        return synergies
    
    def _find_synergy_cards(self, theme1: ThemeNode, theme2: ThemeNode) -> List[str]:
        """Find cards that work well with both themes"""
        # This could be expanded with more sophisticated logic
        return [
            card for card in theme1.key_cards
            if any(pattern in card.lower() for pattern in theme2.synergy_patterns)
        ] 