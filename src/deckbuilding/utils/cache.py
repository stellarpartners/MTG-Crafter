from pathlib import Path
import json
from typing import Dict, Optional

class CacheManager:
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def load_cache(self, name: str) -> Optional[Dict]:
        cache_file = self.cache_dir / f"{name}.json"
        if cache_file.exists():
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def save_cache(self, name: str, data: Dict):
        cache_file = self.cache_dir / f"{name}.json"
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2) 