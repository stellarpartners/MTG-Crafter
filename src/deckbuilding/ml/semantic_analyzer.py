from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from tqdm import tqdm
from pathlib import Path
from collections import defaultdict
import re

class SemanticThemeAnalyzer:
    def __init__(self):
        # Check for GPU
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"Using device: {self.device}")
        
        try:
            # Load models and move to GPU
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            self.embedding_model.to(self.device)
            
            # Clear CUDA cache after model loading
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
        except Exception as e:
            print(f"Error loading models: {str(e)}")
            raise SystemExit(1)
        
        # Initialize BERT classifier with proper configuration
        self.tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
        self.classifier = AutoModelForSequenceClassification.from_pretrained(
            "bert-base-uncased",
            num_labels=2,  # Binary classification (fits theme or not)
            problem_type="single_label_classification",
            classifier_dropout=0.2
        )
        
        # Initialize the classification head weights properly
        self.classifier.classifier.weight.data.normal_(mean=0.0, std=0.02)
        self.classifier.classifier.bias.data.zero_()
        
        self.classifier.to(self.device)
        
        # Load pretrained weights if they exist
        model_path = Path("data/models/theme_classifier.pth")
        if model_path.exists():
            print("Loading pretrained theme classifier...")
            self.classifier.load_state_dict(torch.load(str(model_path)))
            self.classifier.eval()
        else:
            print("No pretrained theme classifier found. Model will need training.")
            print("Run setup/training to improve suggestions.")
        
        # Enable GPU optimizations
        if torch.cuda.is_available():
            # Enable cudnn autotuner
            torch.backends.cudnn.benchmark = True
            # Use mixed precision training (new syntax)
            self.scaler = torch.amp.GradScaler('cuda')
        
        # Batch processing settings
        self.batch_size = 32  # Adjust based on your GPU memory
        
        # Cache embeddings in GPU memory
        self.embedding_cache = {}
        
        # Define semantic connections
        self.semantic_groups = {
            'power': [
                '+1/+1 counter', 'power', 'toughness', 'strengthen',
                'gets bigger', 'grows', 'boost'
            ],
            'counters': [
                'add counters', 'remove counters', 'double counters',
                'proliferate', 'adapt', 'evolve', 'support',
                'strengthen', 'grow', 'enhance'
            ],
            'graveyard': [
                'return from graveyard', 'exile from graveyard',
                'dredge', 'delve', 'escape', 'flashback',
                'unearth', 'scavenge', 'aftermath'
            ],
            'sacrifice': [
                'sacrifice', 'dies', 'when a creature dies',
                'when enters the graveyard', 'death trigger'
            ],
            'self_mill': [
                'put cards into graveyard', 'mill yourself',
                'put top cards into graveyard', 'dredge'
            ]
        }
        
        # Define keyword patterns to look for
        self.keyword_patterns = {
            'counters': [r'\+1/\+1', r'-1/-1', r'counter'],
            'graveyard': [r'graveyard', r'dies', r'died', r'death'],
            'sacrifice': [r'sacrifice', r'sacrificed'],
            'power_matters': [r'power', r'toughness', r'\+\d+/\+\d+'],
        }
    
    def __del__(self):
        """Cleanup GPU memory"""
        if hasattr(self, 'embedding_model'):
            self.embedding_model.cpu()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    
    def batch_encode_texts(self, texts: List[str]) -> torch.Tensor:
        """Encode multiple texts in batches"""
        all_embeddings = []
        
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            with torch.amp.autocast(device_type='cuda', dtype=torch.float16):
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
        # First extract direct keywords
        keywords = self._extract_keywords(card_text)
        if keywords:
            reasons = [f"Contains {theme} keyword: {', '.join(words)}" 
                      for theme, words in keywords.items()]
        else:
            reasons = []
        
        # Get card embedding
        with torch.amp.autocast(device_type='cuda', dtype=torch.float16):
            card_embedding = self.embedding_model.encode(
                card_text,
                convert_to_tensor=True
            ).to(self.device)
        
        # Get theme embedding (from cache if available)
        theme_key = theme_description.split()[0]
        if theme_key in self.embedding_cache:
            theme_embedding = self.embedding_cache[theme_key]
        else:
            with torch.amp.autocast(device_type='cuda', dtype=torch.float16):
                theme_embedding = self.embedding_model.encode(
                    theme_description,
                    convert_to_tensor=True
                ).to(self.device)
        
        # Calculate similarity using GPU
        similarity = torch.nn.functional.cosine_similarity(
            card_embedding.unsqueeze(0),
            theme_embedding.unsqueeze(0)
        ).item()
        
        # Add semantic matches
        reasons.extend(self._batch_semantic_matches(card_text))
        
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
        with torch.amp.autocast(device_type='cuda', dtype=torch.float16):
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
    
    def _extract_keywords(self, text: str) -> Dict[str, List[str]]:
        """Extract keywords from card text using regex patterns"""
        text = text.lower()
        found_keywords = defaultdict(list)
        
        for theme, patterns in self.keyword_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text)
                if matches:
                    found_keywords[theme].extend(matches)
        
        return found_keywords
    
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
                with torch.amp.autocast(device_type='cuda', dtype=torch.float16):
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