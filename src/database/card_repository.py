"""
Card Repository - Centralized API for querying the Card Database.

This module centralizes all database interactions. All other components should use 
this repository for accessing card data.
"""

from typing import Optional, Dict, List
from src.database.card_database import CardDatabase

class CardRepository:
    def __init__(self, db: Optional[CardDatabase] = None):
        # Use an existing CardDatabase instance if provided; otherwise, instantiate one.
        self.db = db if db is not None else CardDatabase()
    
    def get_card(self, card_name: str) -> Optional[Dict]:
        """Retrieve card information by name (case-insensitive)"""
        # Pass-through to the CardDatabase's get_card method.
        return self.db.get_card(card_name)
    
    def search_cards(self, query: str) -> List[Dict]:
        """
        Search for cards matching the query string.
        The exact implementation details can be abstracted inside the CardDatabase.
        """
        return self.db.search_cards(query)
    
    def needs_update(self) -> bool:
        """Check if the database needs to be updated."""
        return self.db.needs_update()
    
    def close(self):
        """Close the database connection."""
        self.db.close() 