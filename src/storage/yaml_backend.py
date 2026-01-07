"""YAML-based file storage backend."""

import os
import yaml
import aiofiles
from pathlib import Path
from typing import Any, List, Optional

from src.storage.base import StorageBackend


class YAMLBackend(StorageBackend):
    """File-based storage using YAML format."""
    
    def __init__(self, storage_dir: str = "./data"):
        """
        Initialize YAML storage backend.
        
        Args:
            storage_dir: Directory to store YAML files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_file_path(self, key: str) -> Path:
        """
        Get the file path for a given key.
        
        Args:
            key: Storage key
            
        Returns:
            Path object for the storage file
        """
        # Replace slashes with double underscores to support namespaced keys
        safe_key = key.replace("/", "__")
        return self.storage_dir / f"{safe_key}.yaml"
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value by key from YAML file.
        
        Args:
            key: The key to retrieve
            
        Returns:
            The value if it exists, None otherwise
        """
        file_path = self._get_file_path(key)
        
        if not file_path.exists():
            return None
        
        try:
            async with aiofiles.open(file_path, 'r') as f:
                content = await f.read()
                data = yaml.safe_load(content)
                return data
        except Exception:
            return None
    
    async def set(self, key: str, value: Any) -> None:
        """
        Store a value with the given key in YAML file.
        
        Args:
            key: The key to store under
            value: The value to store
        """
        file_path = self._get_file_path(key)
        
        try:
            # Convert value to JSON-serializable format first
            # This handles UUIDs, datetimes, and other non-YAML types
            import json
            from datetime import datetime
            from uuid import UUID
            
            def convert_value(obj):
                """Convert complex types to serializable formats."""
                if isinstance(obj, dict):
                    return {k: convert_value(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_value(item) for item in obj]
                elif isinstance(obj, UUID):
                    return str(obj)
                elif isinstance(obj, datetime):
                    return obj.isoformat()
                else:
                    return obj
            
            serializable_value = convert_value(value)
            
            async with aiofiles.open(file_path, 'w') as f:
                yaml_content = yaml.safe_dump(serializable_value, default_flow_style=False)
                await f.write(yaml_content)
        except Exception as e:
            raise RuntimeError(f"Failed to write YAML file: {e}")
    
    async def delete(self, key: str) -> bool:
        """
        Delete a value by key.
        
        Args:
            key: The key to delete
            
        Returns:
            True if the key was deleted, False if it didn't exist
        """
        file_path = self._get_file_path(key)
        
        if not file_path.exists():
            return False
        
        try:
            file_path.unlink()
            return True
        except Exception:
            return False
    
    async def list(self, prefix: str = "") -> List[str]:
        """
        List all keys with the given prefix.
        
        Args:
            prefix: The prefix to filter by (empty string for all keys)
            
        Returns:
            List of keys matching the prefix
        """
        keys = []
        
        for file_path in self.storage_dir.glob("*.yaml"):
            # Extract key from filename (remove .yaml extension)
            safe_key = file_path.stem
            
            # Convert back to original format (double underscores to slashes)
            original_key = safe_key.replace("__", "/")
            
            # Check prefix match
            if not prefix or original_key.startswith(prefix):
                keys.append(original_key)
        
        return sorted(keys)
    
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists.
        
        Args:
            key: The key to check
            
        Returns:
            True if the key exists, False otherwise
        """
        file_path = self._get_file_path(key)
        return file_path.exists()
