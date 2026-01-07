"""Tests for user registry."""

import pytest
import tempfile
import shutil

from src.auth.models import UserCreate
from src.registry.user_registry import UserRegistry
from src.storage.yaml_backend import YAMLBackend


class TestUserRegistry:
    """Test user registry."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)
    
    @pytest.fixture
    def storage(self, temp_dir):
        """Create a storage backend."""
        return YAMLBackend(storage_dir=temp_dir)
    
    @pytest.fixture
    def registry(self, storage):
        """Create a user registry."""
        return UserRegistry(storage=storage)
    
    @pytest.mark.asyncio
    async def test_create_user(self, registry):
        """Test creating a user."""
        user_create = UserCreate(
            email="test@example.com",
            display_name="Test User",
            password="password123",
            git_name="Test User",
            git_email="test@example.com"
        )
        
        user = await registry.create(user_create)
        
        assert user.email == "test@example.com"
        assert user.display_name == "Test User"
    
    @pytest.mark.asyncio
    async def test_get_user(self, registry):
        """Test getting a user by ID."""
        user_create = UserCreate(
            email="test@example.com",
            display_name="Test User",
            password="password123",
            git_name="Test User",
            git_email="test@example.com"
        )
        
        created = await registry.create(user_create)
        retrieved = await registry.get(created.id)
        
        assert retrieved is not None
        assert retrieved.id == created.id
    
    @pytest.mark.asyncio
    async def test_get_by_email(self, registry):
        """Test getting a user by email."""
        user_create = UserCreate(
            email="test@example.com",
            display_name="Test User",
            password="password123",
            git_name="Test User",
            git_email="test@example.com"
        )
        
        created = await registry.create(user_create)
        retrieved = await registry.get_by_email("test@example.com")
        
        assert retrieved is not None
        assert retrieved.id == created.id
    
    @pytest.mark.asyncio
    async def test_update_user(self, registry):
        """Test updating a user."""
        user_create = UserCreate(
            email="test@example.com",
            display_name="Test User",
            password="password123",
            git_name="Test User",
            git_email="test@example.com"
        )
        
        created = await registry.create(user_create)
        updated = await registry.update(
            created.id,
            display_name="Updated Name"
        )
        
        assert updated is not None
        assert updated.display_name == "Updated Name"
    
    @pytest.mark.asyncio
    async def test_delete_user(self, registry):
        """Test deleting a user."""
        user_create = UserCreate(
            email="test@example.com",
            display_name="Test User",
            password="password123",
            git_name="Test User",
            git_email="test@example.com"
        )
        
        created = await registry.create(user_create)
        
        # Delete user
        success = await registry.delete(created.id)
        assert success is True
        
        # Verify user is gone
        retrieved = await registry.get(created.id)
        assert retrieved is None
    
    @pytest.mark.asyncio
    async def test_list_all_users(self, registry):
        """Test listing all users."""
        # Create multiple users
        for i in range(3):
            user_create = UserCreate(
                email=f"user{i}@example.com",
                display_name=f"User {i}",
                password="password123",
                git_name=f"User {i}",
                git_email=f"user{i}@example.com"
            )
            await registry.create(user_create)
        
        # List all users
        users = await registry.list_all()
        
        assert len(users) == 3
        assert all(user.email.startswith("user") for user in users)
