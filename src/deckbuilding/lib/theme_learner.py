from typing import Dict, List, Set, Tuple, Optional
import torch
from sentence_transformers import SentenceTransformer
from sklearn.cluster import DBSCAN
from collections import defaultdict
from tqdm import tqdm
import numpy as np
from dataclasses import dataclass
import re

@dataclass
class DiscoveredTheme:
    name: str
    description: str
    keywords: List[str]
    key_cards: List[str]
    related_patterns: List[str]
    similarity_score: float

class ThemeLearner:
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.embedding_model.to(self.device)
        
        # Cache for computed embeddings
        self.card_embeddings = {}
        self.pattern_embeddings = {}
        
    def discover_themes(self, oracle_data: Dict) -> Dict[str, DiscoveredTheme]:
        """Discover themes from card data"""
        print("Discovering themes from card data...")
        
        # Extract text patterns and keywords
        patterns = self._extract_patterns(oracle_data)
        
        # Create embeddings for all cards
        card_texts = []
        oracle_ids = []
        
        print("Creating card embeddings...")
        for oracle_id, card in tqdm(oracle_data['cards'].items()):
            text = f"{card['name']} {card.get('oracle_text', '')}"
            card_texts.append(text)
            oracle_ids.append(oracle_id)
        
        # Batch process embeddings
        embeddings = self._batch_encode(card_texts)
        
        # Cluster cards to find themes
        print("\nClustering cards into themes...")
        clusters = self._cluster_cards(embeddings)
        
        # Analyze each cluster to identify themes
        themes = {}
        for cluster_id in np.unique(clusters):
            if cluster_id == -1:  # Noise points in DBSCAN
                continue
                
            # Get cards in this cluster
            cluster_indices = np.where(clusters == cluster_id)[0]
            cluster_cards = [oracle_data['cards'][oracle_ids[i]] for i in cluster_indices]
            
            # Analyze cluster to identify theme
            theme = self._analyze_cluster(cluster_cards, patterns)
            if theme:
                themes[theme.name] = theme
        
        return themes
    
    def _extract_patterns(self, oracle_data: Dict) -> List[str]:
        """Extract common text patterns from cards"""
        patterns = defaultdict(int)
        
        for card in oracle_data['cards'].values():
            text = card.get('oracle_text', '')
            if not text:
                continue
            
            # Extract mechanical themes
            mechanical_patterns = [
                (r'\+1/\+1', 'counters'),
                (r'graveyard', 'graveyard'),
                (r'sacrifice', 'sacrifice'),
                (r'dies', 'death_triggers'),
                (r'power', 'power_matters'),
                (r'when ~ enters', 'etb_triggers'),
                (r'when ~ attacks', 'attack_triggers')
            ]
            
            for pattern, theme in mechanical_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    patterns[theme] += 1
            
            # Extract patterns using rules
            # 1. Trigger patterns
            if 'whenever' in text.lower():
                parts = text.lower().split('whenever')
                if len(parts) > 1:
                    trigger_text = parts[1].strip()
                    # Use comma if available; otherwise use the first word
                    if ',' in trigger_text:
                        trigger = trigger_text.split(',')[0].strip()
                    else:
                        trigger_words = trigger_text.split()
                        trigger = trigger_words[0] if trigger_words else ""
                    if trigger:
                        patterns[f"whenever {trigger}"] += 1
                        
            # 2. Keyword actions
            keywords = card.get('keywords', [])
            for keyword in keywords:
                patterns[keyword.lower()] += 1
            
            # 3. Common phrases
            phrases = [
                'enters the battlefield',
                'dies',
                'sacrifice',
                'counter',
                'graveyard',
                'exile'
            ]
            for phrase in phrases:
                if phrase in text.lower():
                    patterns[phrase] += 1
        
        # Keep only significant patterns
        return [p for p, count in patterns.items() if count > 5]
    
    def _batch_encode(self, texts: List[str], batch_size: int = 32) -> torch.Tensor:
        """Encode texts in batches"""
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            with torch.cuda.amp.autocast():
                embeddings = self.embedding_model.encode(
                    batch,
                    convert_to_tensor=True,
                    show_progress_bar=False
                )
                all_embeddings.append(embeddings)
        
        return torch.cat(all_embeddings)
    
    def _cluster_cards(self, embeddings: torch.Tensor) -> np.ndarray:
        """Cluster cards based on their embeddings"""
        # Convert to numpy for sklearn
        embeddings_np = embeddings.cpu().numpy()
        
        # Use DBSCAN for clustering (automatically determines number of clusters)
        clustering = DBSCAN(
            eps=0.3,  # Distance threshold
            min_samples=5,  # Minimum cards for a theme
            metric='cosine'
        )
        
        return clustering.fit_predict(embeddings_np)
    
    def _analyze_cluster(self, cards: List[Dict], patterns: List[str]) -> Optional[DiscoveredTheme]:
        """Analyze a cluster to identify its theme"""
        # Combine all text from cluster
        texts = [f"{card['name']} {card.get('oracle_text', '')}" for card in cards]
        combined_text = " ".join(texts)
        
        # Find common patterns
        cluster_patterns = []
        for pattern in patterns:
            if combined_text.count(pattern) > len(cards) * 0.3:  # At least 30% of cards
                cluster_patterns.append(pattern)
        
        if not cluster_patterns:
            return None
        
        # Find key cards (most representative of patterns)
        key_cards = []
        for card in cards:
            pattern_matches = sum(1 for p in cluster_patterns if p in card.get('oracle_text', '').lower())
            if pattern_matches >= 2:
                key_cards.append(card['name'])
        
        # Generate theme name and description
        main_patterns = sorted(cluster_patterns, key=lambda p: combined_text.count(p), reverse=True)
        theme_name = main_patterns[0].replace(' ', '_')
        
        return DiscoveredTheme(
            name=theme_name,
            description=f"Theme based on {', '.join(main_patterns[:3])}",
            keywords=cluster_patterns,
            key_cards=key_cards[:5],
            related_patterns=main_patterns,
            similarity_score=len(cluster_patterns) / len(patterns)
        )
    
    def find_theme_relationships(self, themes: Dict[str, DiscoveredTheme]) -> List[Tuple[str, str, float]]:
        """Find relationships between discovered themes"""
        relationships = []
        
        theme_items = list(themes.items())
        for i, (name1, theme1) in enumerate(theme_items):
            for name2, theme2 in theme_items[i+1:]:
                # Calculate similarity based on shared patterns and keywords
                shared_patterns = set(theme1.related_patterns) & set(theme2.related_patterns)
                shared_keywords = set(theme1.keywords) & set(theme2.keywords)
                
                similarity = (len(shared_patterns) + len(shared_keywords)) / \
                           (len(theme1.related_patterns) + len(theme1.keywords))
                
                if similarity > 0.2:  # Threshold for relationship
                    relationships.append((name1, name2, similarity))
        
        return sorted(relationships, key=lambda x: x[2], reverse=True) 