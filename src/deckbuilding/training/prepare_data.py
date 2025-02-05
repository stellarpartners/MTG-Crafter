from pathlib import Path
import json
import torch
from typing import Dict
from tqdm import tqdm
from sentence_transformers import SentenceTransformer

def extract_oracle_texts(cache_dir: Path = Path("data/training")):
    """Extract and save unique oracle texts"""
    cache_dir.mkdir(parents=True, exist_ok=True)
    # ... rest of the code ...

def create_embeddings(oracle_texts: Dict, model_dir: Path = Path("data/training/models")):
    """Create and save embeddings"""
    model_dir.mkdir(parents=True, exist_ok=True)
    # ... rest of the code ... 