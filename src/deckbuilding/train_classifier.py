import torch
from pathlib import Path
import json
from tqdm import tqdm
from .semantic_analyzer import SemanticThemeAnalyzer

def train_theme_classifier():
    """Train the theme classifier on our examples"""
    print("Loading training data...")
    
    # Load examples
    with open("data/training/theme_examples.json", 'r') as f:
        examples = json.load(f)
    
    # Load oracle embeddings
    embeddings_data = torch.load("data/training/oracle_embeddings.pt")
    
    # Initialize analyzer
    analyzer = SemanticThemeAnalyzer()
    
    print(f"Training on {len(examples)} examples...")
    analyzer.train_on_examples(examples, epochs=5)
    
    # Create models directory and save
    models_dir = Path("data/models")
    models_dir.mkdir(parents=True, exist_ok=True)
    
    model_path = models_dir / "theme_classifier.pth"
    torch.save(analyzer.classifier.state_dict(), str(model_path))
    print(f"Model saved to {model_path}")
    print("Training complete!")

if __name__ == "__main__":
    train_theme_classifier() 