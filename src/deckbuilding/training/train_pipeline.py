from pathlib import Path
import time
from typing import Callable
from tqdm import tqdm

from .prepare_data import extract_oracle_texts, create_embeddings
from .theme_trainer import ThemeTrainer

class TrainingPipeline:
    def __init__(self):
        self.data_dir = Path("data/training")
        self.model_dir = self.data_dir / "models"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.model_dir.mkdir(parents=True, exist_ok=True)
    
    def run_step(self, name: str, func: Callable, *args, **kwargs):
        """Run a pipeline step with timing and error handling"""
        print(f"\n{'='*20} {name} {'='*20}")
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            print(f"\n✓ {name} completed in {duration:.1f} seconds")
            return result
        except Exception as e:
            print(f"\n✗ Error in {name}: {e}")
            raise
    
    def run_pipeline(self, force_retrain: bool = False):
        """Run complete training pipeline"""
        print("\nStarting MTG Theme Classifier Training Pipeline")
        print("="*50)
        
        # Step 1: Extract oracle texts
        oracle_texts = self.run_step(
            "Extracting Oracle Texts",
            extract_oracle_texts,
            self.data_dir
        )
        
        # Step 2: Create embeddings
        if oracle_texts:
            self.run_step(
                "Creating Embeddings",
                create_embeddings,
                oracle_texts,
                self.model_dir
            )
        
        # Step 3: Train theme classifier
        if force_retrain or not (self.model_dir / "theme_classifier.pth").exists():
            trainer = ThemeTrainer()
            self.run_step(
                "Training Theme Classifier",
                trainer.train,
                oracle_texts,
                epochs=5
            )
        
        print("\n" + "="*50)
        print("Pipeline completed successfully!")
        print("="*50) 