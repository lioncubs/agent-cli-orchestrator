"""Tests for YAML storage backend."""

import pytest
import tempfile
import shutil
from pathlib import Path

from src.storage.yaml_backend import YAMLBackend


class TestYAMLBackend:
    """Test YAML storage backend."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)
    
    @pytest.fixture
    def storage(self, temp_dir):
        """Create a YAML storage backend."""
        return YAMLBackend(storage_dir=temp_dir)
    
    @pytest.mark.asyncio
    async def test_set_and_get(self, storage):
        """Test setting and getting a value."""
        key = "test_key"
        value = {"name": "test", "value": 123}
        
        await storage.set(key, value)
        result = await storage.get(key)
        
        assert result == value
    
    @pytest.mark.asyncio
    async def test_get_nonexistent(self, storage):
        """Test getting a nonexistent key."""
        result = await storage.get("nonexistent")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_exists(self, storage):
        """Test checking if a key exists."""
        key = "test_key"
        
        # Key doesn't exist yet
        assert await storage.exists(key) is False
        
        # Create key
        await storage.set(key, {"data": "test"})
        
        # Key exists now
        assert await storage.exists(key) is True
    
    @pytest.mark.asyncio
    async def test_delete(self, storage):
        """Test deleting a key."""
        key = "test_key"
        
        # Create key
        await storage.set(key, {"data": "test"})
        assert await storage.exists(key) is True
        
        # Delete key
        result = await storage.delete(key)
        assert result is True
        assert await storage.exists(key) is False
        
        # Try to delete again
        result = await storage.delete(key)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_list_all(self, storage):
        """Test listing all keys."""
        # Create multiple keys
        await storage.set("key1", {"data": 1})
        await storage.set("key2", {"data": 2})
        await storage.set("key3", {"data": 3})
        
        keys = await storage.list()
        assert len(keys) == 3
        assert "key1" in keys
        assert "key2" in keys
        assert "key3" in keys
    
    @pytest.mark.asyncio
    async def test_list_with_prefix(self, storage):
        """Test listing keys with a prefix."""
        # Create keys with different prefixes
        await storage.set("users/1", {"name": "user1"})
        await storage.set("users/2", {"name": "user2"})
        await storage.set("posts/1", {"title": "post1"})
        
        # List all keys
        all_keys = await storage.list()
        assert len(all_keys) == 3
        
        # List only user keys
        user_keys = await storage.list("users")
        assert len(user_keys) == 2
        assert "users/1" in user_keys
        assert "users/2" in user_keys
        
        # List only post keys
        post_keys = await storage.list("posts")
        assert len(post_keys) == 1
        assert "posts/1" in post_keys
    
    @pytest.mark.asyncio
    async def test_complex_data(self, storage):
        """Test storing complex nested data."""
        key = "complex"
        value = {
            "string": "test",
            "number": 123,
            "float": 45.67,
            "boolean": True,
            "null": None,
            "list": [1, 2, 3],
            "nested": {
                "key": "value",
                "list": ["a", "b", "c"]
            }
        }
        
        await storage.set(key, value)
        result = await storage.get(key)
        
        assert result == value
    
    @pytest.mark.asyncio
    async def test_overwrite(self, storage):
        """Test overwriting an existing key."""
        key = "test_key"
        
        # Set initial value
        await storage.set(key, {"version": 1})
        result = await storage.get(key)
        assert result["version"] == 1
        
        # Overwrite with new value
        await storage.set(key, {"version": 2})
        result = await storage.get(key)
        assert result["version"] == 2
    
    @pytest.mark.asyncio
    async def test_namespaced_keys(self, storage):
        """Test keys with namespace separators."""
        # Create keys with slashes
        await storage.set("namespace/sub/key1", {"data": 1})
        await storage.set("namespace/sub/key2", {"data": 2})
        
        # Verify they can be retrieved
        result1 = await storage.get("namespace/sub/key1")
        result2 = await storage.get("namespace/sub/key2")
        
        assert result1["data"] == 1
        assert result2["data"] == 2
        
        # Verify they can be listed
        keys = await storage.list("namespace")
        assert len(keys) == 2
