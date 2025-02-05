from pathlib import Path
import json
from typing import List, Dict, Set
from tqdm import tqdm
import torch
from sentence_transformers import SentenceTransformer

def extract_oracle_texts():
    """Extract all unique oracle texts from card data"""
    print("Extracting unique oracle texts...")
    
    # Get all set files
    sets_dir = Path("cache/scryfall/sets")
    if not sets_dir.exists():
        print("No card data found! Please run data collection first.")
        return
    
    # Track unique texts
    oracle_texts: Dict[str, Dict] = {}  # oracle_id -> card data
    
    # Process each set
    set_files = list(sets_dir.glob("*.json"))
    print(f"Processing {len(set_files)} sets...")
    
    for set_file in tqdm(set_files):
        try:
            with open(set_file, 'r', encoding='utf-8') as f:
                cards = json.load(f)
                
            for card in cards:
                if 'oracle_id' not in card or not card.get('oracle_text'):
                    continue
                    
                oracle_id = card['oracle_id']
                if oracle_id not in oracle_texts:
                    oracle_texts[oracle_id] = {
                        'name': card['name'],
                        'oracle_text': card['oracle_text'],
                        'type_line': card.get('type_line', ''),
                        'mana_cost': card.get('mana_cost', ''),
                        'color_identity': card.get('color_identity', []),
                        'keywords': card.get('keywords', []),
                        'first_printing': card.get('released_at')
                    }
        
        except Exception as e:
            print(f"Error processing {set_file}: {e}")
    
    # Save to file
    output_file = Path("data/training/oracle_texts.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'count': len(oracle_texts),
            'cards': oracle_texts
        }, f, indent=2)
    
    print(f"\nExtracted {len(oracle_texts)} unique oracle texts")
    return oracle_texts

def create_embeddings(oracle_texts: Dict[str, Dict]):
    """Create embeddings for all oracle texts"""
    print("\nCreating embeddings...")
    
    # Initialize model with GPU
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = SentenceTransformer('all-MiniLM-L6-v2')
    model.to(device)
    
    # Prepare texts
    texts = []
    oracle_ids = []
    
    for oracle_id, card in oracle_texts.items():
        # Combine relevant text fields
        text = f"{card['name']} {card['type_line']} {card['oracle_text']}"
        texts.append(text)
        oracle_ids.append(oracle_id)
    
    # Create embeddings in batches
    batch_size = 32
    all_embeddings = []
    
    for i in tqdm(range(0, len(texts), batch_size)):
        batch = texts[i:i + batch_size]
        with torch.cuda.amp.autocast():
            embeddings = model.encode(
                batch,
                convert_to_tensor=True,
                show_progress_bar=False
            )
            all_embeddings.append(embeddings.cpu())  # Move to CPU for storage
    
    # Combine all embeddings
    embeddings_tensor = torch.cat(all_embeddings)
    
    # Save embeddings
    torch.save({
        'embeddings': embeddings_tensor,
        'oracle_ids': oracle_ids
    }, 'data/training/oracle_embeddings.pt')
    
    print(f"Created embeddings for {len(texts)} cards")

if __name__ == "__main__":
    print("Preparing training data...")
    oracle_texts = extract_oracle_texts()
    if oracle_texts:
        create_embeddings(oracle_texts)
    print("\nDone!") 