from typing import List, Dict, Set
from collections import defaultdict
from dataclasses import dataclass

from .models import DeckTheme, ColorIdentity
from .semantic_analyzer import SemanticThemeAnalyzer

@dataclass
class ThemeMatch:
    theme: DeckTheme
    confidence: float
    reasons: List[str]

class ThemeClassifier:
    def __init__(self, themes: Dict[str, List[DeckTheme]]):
        self.themes = themes
        self.theme_index = self._build_theme_index()
        self.semantic_analyzer = SemanticThemeAnalyzer()
    
    def _build_theme_index(self) -> Dict[str, Set[str]]:
        """Build keyword index for each theme"""
        index = defaultdict(set)
        
        for category, theme_list in self.themes.items():
            for theme in theme_list:
                # Add all keywords
                for keyword in theme.key_keywords:
                    index[keyword.lower()].add(theme.name)
                # Add key card names
                for card in theme.key_cards:
                    index[card.lower()].add(theme.name)
        
        return index
    
    def classify_card(self, card: Dict) -> List[ThemeMatch]:
        """Find themes that match a card"""
        matches = defaultdict(lambda: {'score': 0.0, 'reasons': []})
        
        # Check color identity
        card_colors = set(card.get('color_identity', []))
        
        # Check card text for theme keywords
        card_text = (card.get('oracle_text', '') or '').lower()
        card_name = card.get('name', '').lower()
        card_type = card.get('type_line', '').lower()
        
        # Score each theme
        for category, theme_list in self.themes.items():
            for theme in theme_list:
                # Skip if colors don't match
                theme_colors = {c.value for c in theme.colors}
                if not theme_colors.issubset(card_colors):
                    continue
                
                score = 0.0
                reasons = []
                
                # Check key cards
                if card_name in {k.lower() for k in theme.key_cards}:
                    score += 1.0
                    reasons.append("Key card for theme")
                
                # Check keywords in text
                for keyword in theme.key_keywords:
                    keyword = keyword.lower()
                    if keyword in card_text:
                        score += 0.3
                        reasons.append(f"Contains keyword: {keyword}")
                    if keyword in card_type:
                        score += 0.2
                        reasons.append(f"Type line contains: {keyword}")
                
                if score > 0:
                    matches[theme.name] = {
                        'theme': theme,
                        'score': score,
                        'reasons': reasons
                    }
        
        # Add semantic analysis
        card_text = f"{card['name']} {card.get('oracle_text', '')}"
        for category, theme_list in self.themes.items():
            for theme in theme_list:
                theme_desc = f"{theme.name} {theme.description}"
                
                # Get semantic match
                similarity, semantic_reasons = self.semantic_analyzer.analyze_card_theme_fit(
                    card_text, theme_desc
                )
                
                if similarity > 0.6:  # Threshold
                    matches[theme.name]['score'] += similarity
                    matches[theme.name]['reasons'].extend(semantic_reasons)
        
        # Convert to sorted list of matches
        results = []
        for name, data in matches.items():
            if data['score'] >= 0.2:  # Minimum confidence threshold
                results.append(ThemeMatch(
                    theme=data['theme'],
                    confidence=min(1.0, data['score']),
                    reasons=data['reasons']
                ))
        
        return sorted(results, key=lambda x: x.confidence, reverse=True)

    def get_theme_cards(self, theme: DeckTheme, cards: List[Dict]) -> List[Dict]:
        """Find all cards that match a theme"""
        matching_cards = []
        
        for card in cards:
            matches = self.classify_card(card)
            for match in matches:
                if match.theme.name == theme.name and match.confidence >= 0.3:
                    matching_cards.append({
                        'card': card,
                        'confidence': match.confidence,
                        'reasons': match.reasons
                    })
        
        return sorted(matching_cards, key=lambda x: x['confidence'], reverse=True) 