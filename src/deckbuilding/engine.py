from typing import List, Dict, Set
from .models import ColorIdentity, DeckTheme
from .theme_classifier import ThemeClassifier

class DeckbuildingEngine:
    def __init__(self, search_engine, theme_collector):
        self.search = search_engine
        self.themes = theme_collector
        self.load_themes()
        self.classifier = ThemeClassifier(self.theme_categories)
    
    def load_themes(self):
        """Load and categorize all themes"""
        self.theme_categories = {
            'guild': self._load_guild_themes(),
            'tribal': self._load_tribal_themes(),
            'mechanic': self._load_mechanic_themes(),
            'strategy': self._load_strategy_themes()
        }
    
    def suggest_themes(self, colors: Set[ColorIdentity]) -> List[DeckTheme]:
        """Suggest themes based on color identity"""
        suggestions = []
        
        # Find themes matching colors
        for category in self.theme_categories.values():
            for theme in category:
                if theme.colors.issubset(colors):
                    suggestions.append(theme)
        
        return sorted(suggestions, key=lambda x: len(x.key_cards), reverse=True)
    
    def find_synergies(self, theme: DeckTheme) -> List[Dict]:
        """Find cards that synergize with a theme"""
        synergies = []
        
        # Search for cards with theme keywords
        for keyword in theme.key_keywords:
            cards = self.search.search_text(keyword)
            for card in cards:
                if self._matches_color_identity(card, theme.colors):
                    synergies.append({
                        'card': card,
                        'reason': f"Contains keyword: {keyword}"
                    })
        
        return synergies
    
    def _matches_color_identity(self, card: Dict, colors: Set[ColorIdentity]) -> bool:
        """Check if a card matches the color identity"""
        card_colors = {ColorIdentity(c) for c in card.get('color_identity', [])}
        return card_colors.issubset(colors)
    
    def _load_guild_themes(self) -> List[DeckTheme]:
        """Load guild-based themes"""
        themes = []
        
        # Golgari (Black-Green)
        themes.append(DeckTheme(
            name="Golgari Graveyard",
            description="Use the graveyard as a resource",
            key_cards=["Golgari Grave-Troll", "Stinkweed Imp"],
            key_keywords=["Dredge", "graveyard", "sacrifice"],
            colors={ColorIdentity.BLACK, ColorIdentity.GREEN}
        ))
        
        # Simic (Blue-Green)
        themes.append(DeckTheme(
            name="Simic +1/+1 Counters",
            description="Grow your creatures with counters",
            key_cards=["Vorel of the Hull Clade", "Zameck Guildmage"],
            key_keywords=["adapt", "evolve", "counter"],
            colors={ColorIdentity.BLUE, ColorIdentity.GREEN}
        ))
        
        return themes
    
    def _load_tribal_themes(self) -> List[DeckTheme]:
        """Load tribal themes"""
        themes = []
        
        # Zombies
        themes.append(DeckTheme(
            name="Zombie Tribal",
            description="Overwhelm with undead hordes",
            key_cards=["Death Baron", "Gravecrawler"],
            key_keywords=["zombie", "decayed", "undead"],
            colors={ColorIdentity.BLACK, ColorIdentity.BLUE}
        ))
        
        # Dragons
        themes.append(DeckTheme(
            name="Dragon Tribal",
            description="Dominate with powerful dragons",
            key_cards=["Dragon Tempest", "Utvara Hellkite"],
            key_keywords=["dragon", "flying", "firebreathing"],
            colors={ColorIdentity.RED}
        ))
        
        return themes
    
    def _load_mechanic_themes(self) -> List[DeckTheme]:
        """Load mechanic-based themes"""
        themes = []
        
        # Sacrifice
        themes.append(DeckTheme(
            name="Aristocrats",
            description="Profit from your creatures dying",
            key_cards=["Blood Artist", "Viscera Seer"],
            key_keywords=["sacrifice", "dies", "death trigger"],
            colors={ColorIdentity.BLACK, ColorIdentity.WHITE}
        ))
        
        # Spellslinger
        themes.append(DeckTheme(
            name="Spellslinger",
            description="Cast lots of instants and sorceries",
            key_cards=["Young Pyromancer", "Talrand, Sky Summoner"],
            key_keywords=["prowess", "instant", "sorcery"],
            colors={ColorIdentity.BLUE, ColorIdentity.RED}
        ))
        
        return themes
    
    def _load_strategy_themes(self) -> List[DeckTheme]:
        """Load strategy-based themes"""
        themes = []
        
        # Control
        themes.append(DeckTheme(
            name="Draw-Go Control",
            description="React to opponents with counterspells and removal",
            key_cards=["Counterspell", "Fact or Fiction"],
            key_keywords=["counter", "draw", "instant"],
            colors={ColorIdentity.BLUE}
        ))
        
        # Tokens
        themes.append(DeckTheme(
            name="Token Swarm",
            description="Create and empower many token creatures",
            key_cards=["Secure the Wastes", "Intangible Virtue"],
            key_keywords=["create", "token", "creature token"],
            colors={ColorIdentity.WHITE, ColorIdentity.GREEN}
        ))
        
        return themes
    
    def find_theme_cards(self, theme: DeckTheme) -> List[Dict]:
        """Find all cards that fit a theme"""
        # Get all cards in theme colors
        cards = []
        for oracle_id, text in self.search.oracle_texts.items():
            card = {
                'name': self.search.oracle_to_name[oracle_id],
                'oracle_id': oracle_id,
                'oracle_text': text,
                'color_identity': self.search.get_card_colors(oracle_id)
            }
            cards.append(card)
        
        # Classify cards by theme
        return self.classifier.get_theme_cards(theme, cards) 