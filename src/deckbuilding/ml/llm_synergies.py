from openai import OpenAI
from typing import List, Dict

class LLMSynergyAnalyzer:
    def __init__(self):
        self.client = OpenAI()
        
    def analyze_synergy(self, card1: Dict, card2: Dict) -> Dict:
        """Use LLM to analyze synergy between cards"""
        prompt = f"""
        Analyze the synergy between these two Magic: The Gathering cards:

        Card 1: {card1['name']}
        Text: {card1['oracle_text']}

        Card 2: {card2['name']}
        Text: {card2['oracle_text']}

        Explain:
        1. Do these cards have synergy?
        2. How do they work together?
        3. Rate their synergy from 0-10
        """
        
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        
        return {
            'analysis': response.choices[0].message.content,
            'cards': [card1['name'], card2['name']]
        } 