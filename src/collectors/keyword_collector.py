import json
from pathlib import Path
from typing import Dict, List, Set
import re

class KeywordCollector:
    """Collects and analyzes keywords from Magic cards"""
    
    def __init__(self, data_dir: str = "data/raw"):
        self.data_dir = Path(data_dir)
        self.processed_dir = Path("data/processed")
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
    def save_json_alphabetically(self, data: Dict, file_path: Path):
        """Save dictionary data to JSON with alphabetically sorted keys"""
        if isinstance(data, dict):
            # Sort the dictionary by keys
            sorted_data = dict(sorted(data.items()))
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(sorted_data, f, indent=2)
        elif isinstance(data, list):
            # Sort the list
            sorted_data = sorted(data)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(sorted_data, f, indent=2)
        else:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

    def collect_keywords_from_cards(self) -> Dict[str, Dict]:
        """Collect keywords from all downloaded cards"""
        keywords = {}
        
        # Process all card files in data directory
        for file_path in self.data_dir.glob("cards_*.json"):
            with open(file_path, 'r', encoding='utf-8') as f:
                cards = json.load(f)
                
            print(f"Processing {file_path.name}...")
            for card in cards:
                # Get explicit keywords from card data
                card_keywords = card.get('keywords', [])
                for keyword in card_keywords:
                    if keyword not in keywords:
                        keywords[keyword] = {
                            'count': 0,
                            'example_card': card['name'],
                            'rules_text': None,
                            'reminder_text': None
                        }
                    keywords[keyword]['count'] += 1
                    
                    # Try to extract reminder text
                    oracle_text = card.get('oracle_text', '')
                    if oracle_text:
                        # Look for reminder text in parentheses after the keyword
                        reminder_pattern = f"{keyword} \\(([^\\)]+)\\)"
                        reminder_match = re.search(reminder_pattern, oracle_text)
                        if reminder_match and not keywords[keyword]['reminder_text']:
                            keywords[keyword]['reminder_text'] = reminder_match.group(1)
        
        # Save processed keywords alphabetically
        output_file = self.processed_dir / "keywords.json"
        self.save_json_alphabetically(keywords, output_file)
            
        return keywords
    
    def extract_ability_words(self) -> Set[str]:
        """Extract ability words (italicized words at start of abilities)"""
        ability_words = set()
        
        for file_path in self.data_dir.glob("cards_*.json"):
            with open(file_path, 'r', encoding='utf-8') as f:
                cards = json.load(f)
            
            for card in cards:
                oracle_text = card.get('oracle_text', '')
                if oracle_text:
                    # Look for italicized words at the start of lines
                    # In oracle text, italics are marked with *asterisks*
                    for line in oracle_text.split('\n'):
                        if line.startswith('*') and '*' in line[1:]:
                            ability_word = line[1:line.index('*', 1)]
                            ability_words.add(ability_word)
        
        # Save ability words alphabetically
        output_file = self.processed_dir / "ability_words.json"
        self.save_json_alphabetically(list(ability_words), output_file)
            
        return ability_words
    
    def extract_rules_text(self, rules_file: str = "rules/MagicCompRules.txt") -> Dict[str, str]:
        """Extract rules text for keywords from comprehensive rules"""
        rules_text = {}
        
        try:
            with open(rules_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Extract Keyword Actions (701)
            action_section = re.search(r"701\. Keyword Actions(.*?)702\.", content, re.DOTALL)
            if action_section:
                actions = re.finditer(r"701\.\d+\. ([^\"]+?)[\n\r]+([^7]+?)(?=701\.\d+\.|702\.)", 
                                    action_section.group(1), re.DOTALL)
                for match in actions:
                    keyword = match.group(1).strip()
                    rule_text = match.group(2).strip()
                    rules_text[keyword] = {
                        'type': 'action',
                        'rules_text': rule_text
                    }
            
            # Extract Keyword Abilities (702)
            ability_section = re.search(r"702\. Keyword Abilities(.*?)703\.", content, re.DOTALL)
            if ability_section:
                abilities = re.finditer(r"702\.\d+\. ([^\"]+?)[\n\r]+([^7]+?)(?=702\.\d+\.|703\.)", 
                                      ability_section.group(1), re.DOTALL)
                for match in abilities:
                    keyword = match.group(1).strip()
                    rule_text = match.group(2).strip()
                    rules_text[keyword] = {
                        'type': 'ability',
                        'rules_text': rule_text
                    }
            
        except FileNotFoundError:
            print(f"Could not find rules file: {rules_file}")
        except Exception as e:
            print(f"Error processing rules file: {e}")
            
        return rules_text
    
    def enrich_keywords(self):
        """Add rules text to keywords and categorize them"""
        # Load existing keywords
        keywords_file = self.processed_dir / "keywords.json"
        if not keywords_file.exists():
            print("No keywords collected yet. Run collect_keywords_from_cards() first.")
            return
            
        with open(keywords_file, 'r', encoding='utf-8') as f:
            keywords = json.load(f)
        
        # Get rules text
        rules_text = self.extract_rules_text()
        
        # Match keywords with rules
        for keyword in keywords:
            # Try exact match
            if keyword in rules_text:
                keywords[keyword]['rules_text'] = rules_text[keyword]['rules_text']
                keywords[keyword]['type'] = rules_text[keyword]['type']
                continue
                
            # Try case-insensitive match
            keyword_lower = keyword.lower()
            for rule_keyword, rule_data in rules_text.items():
                if keyword_lower == rule_keyword.lower():
                    keywords[keyword]['rules_text'] = rule_data['rules_text']
                    keywords[keyword]['type'] = rule_data['type']
                    break
        
        # Save enriched keywords alphabetically
        output_file = self.processed_dir / "keywords_enriched.json"
        self.save_json_alphabetically(keywords, output_file)
            
        return keywords
    
    def analyze_keywords(self):
        """Print analysis of collected keywords"""
        keywords_file = self.processed_dir / "keywords_enriched.json"
        if not keywords_file.exists():
            keywords_file = self.processed_dir / "keywords.json"
            
        if not keywords_file.exists():
            print("No keywords collected yet. Run collect_keywords_from_cards() first.")
            return
            
        with open(keywords_file, 'r', encoding='utf-8') as f:
            keywords = json.load(f)
            
        print("\nKeyword Analysis:")
        print(f"Total unique keywords: {len(keywords)}")
        
        # Count by type
        type_counts = {}
        for keyword, data in keywords.items():
            keyword_type = data.get('type', 'unknown')
            type_counts[keyword_type] = type_counts.get(keyword_type, 0) + 1
            
        print("\nKeywords by type:")
        for type_name, count in type_counts.items():
            print(f"  {type_name}: {count}")
        
        # Sort keywords by frequency
        sorted_keywords = sorted(
            keywords.items(), 
            key=lambda x: x[1]['count'], 
            reverse=True
        )
        
        print("\nTop 10 most common keywords:")
        for keyword, data in sorted_keywords[:10]:
            print(f"\n{keyword}:")
            print(f"  Type: {data.get('type', 'unknown')}")
            print(f"  Count: {data['count']}")
            print(f"  Example card: {data['example_card']}")
            if data['reminder_text']:
                print(f"  Reminder text: {data['reminder_text']}")
            if data.get('rules_text'):
                print(f"  Rules text: {data['rules_text'][:200]}...")

if __name__ == "__main__":
    collector = KeywordCollector()
    
    print("Collecting keywords from cards...")
    keywords = collector.collect_keywords_from_cards()
    
    print("\nExtracting ability words...")
    ability_words = collector.extract_ability_words()
    
    print("\nEnriching keywords with rules text...")
    enriched_keywords = collector.enrich_keywords()
    
    print("\nAnalyzing keywords...")
    collector.analyze_keywords() 