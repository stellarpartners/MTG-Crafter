from pathlib import Path
from src.database.card_database import CardDatabase

class DataEngine:
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.database = CardDatabase(data_dir=str(self.data_dir))  # Initialize database
        self._initialize_collectors()

    def _initialize_collectors(self):
        self.database = CardDatabase(data_dir=str(self.data_dir))  # Pass the data_dir correctly 

    def cleanup(self):
        """Close database connection and perform cleanup"""
        self.database.close()  # Ensure the database connection is closed
        # Add your cleanup logic here, e.g., removing directories 