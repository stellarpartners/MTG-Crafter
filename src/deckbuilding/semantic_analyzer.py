from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from tqdm import tqdm

class SemanticThemeAnalyzer:
    def __init__(self):
        # Check for GPU
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"Using device: {self.device}")
        
        # Load models and move to GPU
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.embedding_model.to(self.device)
        
        self.tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
        self.classifier = AutoModelForSequenceClassification.from_pretrained("bert-base-uncased")
        self.classifier.to(self.device)
        
        # Enable GPU optimizations
        if torch.cuda.is_available():
            # Enable cudnn autotuner
            torch.backends.cudnn.benchmark = True
            # Use mixed precision training
            self.scaler = torch.cuda.amp.GradScaler()
        
        # Batch processing settings
        self.batch_size = 32  # Adjust based on your GPU memory
        
        # Cache embeddings in GPU memory
        self.embedding_cache = {}
        
        # Define semantic connections
        self.semantic_groups = {
            'counters': [
                'add counters', 'remove counters', 'double counters',
                'proliferate', 'adapt', 'evolve', 'support',
                'strengthen', 'grow', 'enhance'
            ],
            'graveyard': [
                'return from graveyard', 'exile from graveyard',
                'dredge', 'delve', 'escape', 'flashback',
                'unearth', 'scavenge', 'aftermath'
            ]
        }
    
    def batch_encode_texts(self, texts: List[str]) -> torch.Tensor:
        """Encode multiple texts in batches"""
        all_embeddings = []
        
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            with torch.cuda.amp.autocast():
                embeddings = self.embedding_model.encode(
                    batch,
                    convert_to_tensor=True,
                    show_progress_bar=False
                )
                all_embeddings.append(embeddings)
        
        return torch.cat(all_embeddings)
    
    def precompute_theme_embeddings(self, themes: List[Dict]):
        """Precompute and cache theme embeddings"""
        print("Precomputing theme embeddings...")
        theme_texts = [f"{t['name']} {t['description']}" for t in themes]
        
        with torch.no_grad():
            embeddings = self.batch_encode_texts(theme_texts)
            for theme, embedding in zip(themes, embeddings):
                self.embedding_cache[theme['name']] = embedding
    
    def analyze_card_theme_fit(self, card_text: str, theme_description: str) -> Tuple[float, List[str]]:
        """Analyze how well a card fits a theme semantically"""
        # Get card embedding
        with torch.cuda.amp.autocast():
            card_embedding = self.embedding_model.encode(
                card_text,
                convert_to_tensor=True
            ).to(self.device)
        
        # Get theme embedding (from cache if available)
        theme_key = theme_description.split()[0]  # Use theme name as key
        if theme_key in self.embedding_cache:
            theme_embedding = self.embedding_cache[theme_key]
        else:
            with torch.cuda.amp.autocast():
                theme_embedding = self.embedding_model.encode(
                    theme_description,
                    convert_to_tensor=True
                ).to(self.device)
        
        # Calculate similarity using GPU
        similarity = torch.nn.functional.cosine_similarity(
            card_embedding.unsqueeze(0),
            theme_embedding.unsqueeze(0)
        ).item()
        
        # Find semantic matches in parallel
        reasons = self._batch_semantic_matches(card_text)
        
        return similarity, reasons
    
    def _batch_semantic_matches(self, text: str) -> List[str]:
        """Check semantic matches in batches"""
        reasons = []
        all_concepts = []
        concept_groups = []
        
        # Prepare batches
        for group_name, concepts in self.semantic_groups.items():
            all_concepts.extend(concepts)
            concept_groups.extend([group_name] * len(concepts))
        
        # Encode text once
        with torch.cuda.amp.autocast():
            text_embedding = self.embedding_model.encode(
                text,
                convert_to_tensor=True
            ).to(self.device)
        
        # Batch encode concepts
        concept_embeddings = self.batch_encode_texts(all_concepts)
        
        # Calculate similarities in one go
        similarities = torch.nn.functional.cosine_similarity(
            text_embedding.unsqueeze(0),
            concept_embeddings
        )
        
        # Find matches
        matches = similarities > 0.7
        for i, is_match in enumerate(matches):
            if is_match:
                group = concept_groups[i]
                concept = all_concepts[i]
                reasons.append(f"Matches {group} concept: {concept}")
        
        return reasons
    
    def train_on_examples(self, examples: List[Dict[str, str]], epochs: int = 3):
        """Train on known good/bad examples using GPU"""
        print("Training theme classifier...")
        
        # Prepare data
        texts = [f"{ex['card_text']} [SEP] {ex['theme']}" for ex in examples]
        labels = torch.tensor([ex['fits'] for ex in examples]).to(self.device)
        
        # Create dataloader
        encodings = self.tokenizer(
            texts,
            truncation=True,
            padding=True,
            return_tensors="pt"
        )
        
        dataset = torch.utils.data.TensorDataset(
            encodings['input_ids'].to(self.device),
            encodings['attention_mask'].to(self.device),
            labels
        )
        
        dataloader = torch.utils.data.DataLoader(
            dataset,
            batch_size=self.batch_size,
            shuffle=True
        )
        
        # Training loop with progress bar
        optimizer = torch.optim.AdamW(self.classifier.parameters())
        
        for epoch in range(epochs):
            print(f"\nEpoch {epoch+1}/{epochs}")
            self.classifier.train()
            
            progress_bar = tqdm(dataloader, desc="Training")
            for batch in progress_bar:
                input_ids, attention_mask, batch_labels = batch
                
                # Mixed precision training
                with torch.cuda.amp.autocast():
                    outputs = self.classifier(
                        input_ids=input_ids,
                        attention_mask=attention_mask,
                        labels=batch_labels
                    )
                    loss = outputs.loss
                
                self.scaler.scale(loss).backward()
                self.scaler.step(optimizer)
                self.scaler.update()
                optimizer.zero_grad()
                
                progress_bar.set_postfix({'loss': f"{loss.item():.4f}"}) 