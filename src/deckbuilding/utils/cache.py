from pathlib import Path
import json
from typing import Dict, Optional
from datetime import datetime

class CacheManager:
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.cache_dir / "metadata.json"
        self._load_metadata()
    
    def _load_metadata(self):
        """Load or initialize cache metadata"""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    self.metadata = json.load(f)
            else:
                self.metadata = {
                    'last_update': None,
                    'version': '1.0',
                    'files': {}
                }
                self._save_metadata()
        except Exception as e:
            print(f"Error loading cache metadata: {str(e)}")
            self.metadata = {
                'last_update': None,
                'version': '1.0',
                'files': {}
            }
    
    def cleanup_orphaned_files(self):
        """Remove cache files not in metadata"""
        for file in self.cache_dir.glob('**/*'):
            if file.is_file() and file != self.metadata_file:
                rel_path = str(file.relative_to(self.cache_dir))
                if rel_path not in self.metadata['files']:
                    file.unlink()
    
    def load_cache(self, name: str) -> Optional[Dict]:
        """Load data from cache with error handling"""
        cache_file = self.cache_dir / f"{name}.json"
        try:
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Update metadata access time
                    self.metadata['files'][str(cache_file.relative_to(self.cache_dir))] = {
                        'last_access': datetime.now().isoformat()
                    }
                    self._save_metadata()
                    return data
            return None
        except Exception as e:
            print(f"Error loading cache '{name}': {str(e)}")
            return None
    
    def save_cache(self, name: str, data: Dict):
        """Save data to cache with error handling"""
        try:
            cache_file = self.cache_dir / f"{name}.json"
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
                # Update metadata
                self.metadata['files'][str(cache_file.relative_to(self.cache_dir))] = {
                    'last_write': datetime.now().isoformat()
                }
                self._save_metadata()
        except Exception as e:
            print(f"Error saving cache '{name}': {str(e)}")

    def _save_metadata(self):
        """Save cache metadata"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f)
        except Exception as e:
            print(f"Error saving cache metadata: {str(e)}") 