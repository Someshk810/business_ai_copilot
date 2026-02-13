"""Helper utility functions."""

from typing import Dict, Any, List
import json


class Helpers:
    """Collection of helper functions."""
    
    @staticmethod
    def parse_json(json_string: str) -> Dict[str, Any]:
        """Parse JSON string safely.
        
        Args:
            json_string: JSON string to parse
            
        Returns:
            Parsed JSON as dictionary
        """
        try:
            return json.loads(json_string)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")
    
    @staticmethod
    def flatten_dict(dict_obj: Dict[str, Any], parent_key: str = "") -> Dict[str, Any]:
        """Flatten a nested dictionary.
        
        Args:
            dict_obj: Dictionary to flatten
            parent_key: Parent key prefix
            
        Returns:
            Flattened dictionary
        """
        items: List[tuple] = []
        for k, v in dict_obj.items():
            new_key = f"{parent_key}.{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(Helpers.flatten_dict(v, new_key).items())
            else:
                items.append((new_key, v))
        return dict(items)
