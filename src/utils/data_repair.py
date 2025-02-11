import json
from pathlib import Path
from datetime import datetime

class DataRepair:
    @staticmethod
    def repair_set_file(file_path: Path) -> bool:
        """Attempt to repair a corrupted set file"""
        try:
            # Read raw content
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_data = f.read()
                
            # Attempt basic JSON repair
            repaired = json.loads(raw_data.strip().rstrip(',') + ']}}')
            
            # Add missing required fields
            if 'object' not in repaired:
                repaired['object'] = 'set'
            if 'card_count' not in repaired:
                repaired['card_count'] = len(repaired.get('data', []))
                
            # Save repaired file
            backup_path = file_path.with_suffix('.bak')
            file_path.replace(backup_path)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(repaired, f, indent=2)
                
            return True
        except Exception as e:
            print(f"Repair failed for {file_path.name}: {str(e)}")
            return False 