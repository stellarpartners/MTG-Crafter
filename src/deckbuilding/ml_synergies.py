from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from typing import List, Dict, Tuple

class SynergyModel:
    def __init__(self, model_name: str = "bert-base-uncased"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        
        # Load our fine-tuned weights if they exist
        try:
            self.model.load_state_dict(torch.load("models/synergy_model.pth"))
        except:
            print("No fine-tuned model found, using base model")
    
    def prepare_training_data(self) -> List[Dict]:
        """Prepare known synergy pairs for training"""
        synergy_pairs = [
            # Known synergies from MTG history
            ("Ashnod's Altar", "Grave Pact", 1),  # Strong synergy
            ("Blood Artist", "Viscera Seer", 1),  # Strong synergy
            ("Lightning Bolt", "Birds of Paradise", 0),  # No synergy
        ]
        
        return [{
            'text': f"{card1} <sep> {card2}",
            'label': label
        } for card1, card2, label in synergy_pairs]
    
    def fine_tune(self, epochs: int = 5):
        """Fine-tune the model on MTG card synergies"""
        training_data = self.prepare_training_data()
        # Training code here...
    
    def predict_synergy(self, card1: Dict, card2: Dict) -> float:
        """Predict synergy score between two cards"""
        text = f"{card1['oracle_text']} <sep> {card2['oracle_text']}"
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            scores = torch.softmax(outputs.logits, dim=1)
            return scores[0][1].item()  # Synergy score 