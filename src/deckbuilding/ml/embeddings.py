from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict

class CardEmbeddings:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.card_embeddings = {}
        
    def embed_cards(self, cards: List[Dict]):
        """Create embeddings for all cards"""
        for card in cards:
            text = f"{card['name']} {card['oracle_text']}"
            self.card_embeddings[card['oracle_id']] = self.model.encode(text)
    
    def find_similar_cards(self, card: Dict, n: int = 10) -> List[Dict]:
        """Find cards with similar embeddings"""
        query_embedding = self.model.encode(f"{card['name']} {card['oracle_text']}")
        
        similarities = []
        for oracle_id, embedding in self.card_embeddings.items():
            similarity = np.dot(query_embedding, embedding)
            similarities.append((oracle_id, similarity))
        
        # Return top N similar cards
        return sorted(similarities, key=lambda x: x[1], reverse=True)[:n] 