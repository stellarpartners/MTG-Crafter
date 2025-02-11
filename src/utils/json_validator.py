import json
from pathlib import Path
from typing import Dict, Any
import jsonschema

class JSONValidator:
    """Validate Scryfall data against JSON schemas"""
    
    SCRYFALL_SET_SCHEMA = {
        "type": "object",
        "required": ["object", "data", "card_count"],
        "properties": {
            "object": {"const": "set"},
            "data": {
                "type": "array",
                "items": {"$ref": "#/definitions/card"}
            },
            "card_count": {"type": "number"},
            "released_at": {"type": "string", "format": "date"},
            "set_type": {"type": "string"}
        },
        "definitions": {
            "card": {
                "type": "object",
                "required": ["name", "mana_cost", "type_line"],
                "properties": {
                    "name": {"type": "string"},
                    "mana_cost": {"type": "string"},
                    "type_line": {"type": "string"},
                    "oracle_text": {"type": "string"},
                    "power": {"type": "string"},
                    "toughness": {"type": "string"},
                    "loyalty": {"type": "string"},
                    "colors": {"type": "array"},
                    "color_identity": {"type": "array"}
                }
            }
        }
    }

    @classmethod
    def validate_set_file(cls, file_path: Path) -> bool:
        """Full validation of a set file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            return cls.validate_set_structure(data)
        except Exception as e:
            print(f"Validation error in {file_path.name}: {str(e)}")
            return False

    @classmethod
    def validate_set_structure(cls, data: Dict[str, Any]) -> bool:
        """Validate against Scryfall set schema"""
        try:
            jsonschema.validate(instance=data, schema=cls.SCRYFALL_SET_SCHEMA)
            return True
        except jsonschema.ValidationError as ve:
            print(f"Schema validation failed: {ve.message}")
            return False
        except Exception as e:
            print(f"Validation error: {str(e)}")
            return False 