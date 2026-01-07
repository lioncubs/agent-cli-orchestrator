"""Tests for authentication service."""

import pytest
import tempfile
import shutil
from datetime import datetime, timedelta
from uuid import uuid4

from src.auth.service import AuthService
from src.auth.models import UserCreate, APIKeyCreate
from src.storage.yaml_backend import YAMLBackend


class TestAuthService:
    """Test authentication service."""
    
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
    def auth_service(self, storage):
        """Create an auth service."""
        return AuthService(storage=storage)
    
    @pytest.mark.asyncio
    async def test_hash_password(self, auth_service):
        """Test password hashing with bcrypt."""
        password = "test_password_123"
        hash1 = auth_service.hash_password(password)
        hash2 = auth_service.hash_password(password)
        
        # Different hashes due to different salts (bcrypt behavior)
        assert hash1 != hash2
        
        # Hash should be different from password
        assert hash1 != password
        
        # Both hashes should verify correctly
        assert auth_service.verify_password(password, hash1) is True
        assert auth_service.verify_password(password, hash2) is True
    
    @pytest.mark.asyncio
    async def test_verify_password_success(self, auth_service):
        """Test successful password verification."""
        password = "test_password"
        password_hash = auth_service.hash_password(password)
        
        assert auth_service.verify_password(password, password_hash) is True
    
    @pytest.mark.asyncio
    async def test_verify_password_failure(self, auth_service):
        """Test failed password verification."""
        password = "test_password"
        wrong_password = "wrong_password"
        password_hash = auth_service.hash_password(password)
        
        assert auth_service.verify_password(wrong_password, password_hash) is False
    
    @pytest.mark.asyncio
    async def test_create_user(self, auth_service):
        """Test creating a user."""
        user_create = UserCreate(
            email="test@example.com",
            display_name="Test User",
            password="password123",
            git_name="Test User",
            git_email="test@example.com"
        )
        
        user = await auth_service.create_user(user_create)
        
        assert user.email == "test@example.com"
        assert user.display_name == "Test User"
        assert user.password_hash != "password123"  # Should be hashed
        assert user.git_identity.name == "Test User"
        assert user.git_identity.email == "test@example.com"
        assert user.default_model == "gpt-4o"
        assert user.permission_tier == "restricted"
    
    @pytest.mark.asyncio
    async def test_create_duplicate_user(self, auth_service):
        """Test creating a user with duplicate email."""
        user_create = UserCreate(
            email="test@example.com",
            display_name="Test User",
            password="password123",
            git_name="Test User",
            git_email="test@example.com"
        )
        
        # Create first user
        await auth_service.create_user(user_create)
        
        # Try to create duplicate
        with pytest.raises(ValueError, match="already exists"):
            await auth_service.create_user(user_create)
    
    @pytest.mark.asyncio
    async def test_get_user(self, auth_service):
        """Test getting a user by ID."""
        user_create = UserCreate(
            email="test@example.com",
            display_name="Test User",
            password="password123",
            git_name="Test User",
            git_email="test@example.com"
        )
        
        created_user = await auth_service.create_user(user_create)
        retrieved_user = await auth_service.get_user(created_user.id)
        
        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
        assert retrieved_user.email == created_user.email
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_user(self, auth_service):
        """Test getting a nonexistent user."""
        user = await auth_service.get_user(uuid4())
        assert user is None
    
    @pytest.mark.asyncio
    async def test_get_user_by_email(self, auth_service):
        """Test getting a user by email."""
        user_create = UserCreate(
            email="test@example.com",
            display_name="Test User",
            password="password123",
            git_name="Test User",
            git_email="test@example.com"
        )
        
        created_user = await auth_service.create_user(user_create)
        retrieved_user = await auth_service.get_user_by_email("test@example.com")
        
        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
    
    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, auth_service):
        """Test successful user authentication."""
        user_create = UserCreate(
            email="test@example.com",
            display_name="Test User",
            password="password123",
            git_name="Test User",
            git_email="test@example.com"
        )
        
        await auth_service.create_user(user_create)
        
        user = await auth_service.authenticate_user("test@example.com", "password123")
        
        assert user is not None
        assert user.email == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, auth_service):
        """Test authentication with wrong password."""
        user_create = UserCreate(
            email="test@example.com",
            display_name="Test User",
            password="password123",
            git_name="Test User",
            git_email="test@example.com"
        )
        
        await auth_service.create_user(user_create)
        
        user = await auth_service.authenticate_user("test@example.com", "wrong_password")
        
        assert user is None
    
    @pytest.mark.asyncio
    async def test_authenticate_nonexistent_user(self, auth_service):
        """Test authentication with nonexistent user."""
        user = await auth_service.authenticate_user("nonexistent@example.com", "password")
        assert user is None
    
    @pytest.mark.asyncio
    async def test_create_api_key(self, auth_service):
        """Test creating an API key."""
        # Create user
        user_create = UserCreate(
            email="test@example.com",
            display_name="Test User",
            password="password123",
            git_name="Test User",
            git_email="test@example.com"
        )
        user = await auth_service.create_user(user_create)
        
        # Create API key
        api_key_create = APIKeyCreate(
            name="Test API Key",
            scopes=["read", "write"]
        )
        
        api_key, plaintext_key = await auth_service.create_api_key(
            user.id,
            api_key_create
        )
        
        assert api_key.name == "Test API Key"
        assert api_key.scopes == ["read", "write"]
        assert api_key.user_id == user.id
        assert plaintext_key is not None
        assert len(plaintext_key) > 0
        assert api_key.key_hash != plaintext_key  # Should be hashed
    
    @pytest.mark.asyncio
    async def test_list_user_api_keys(self, auth_service):
        """Test listing user API keys."""
        # Create user
        user_create = UserCreate(
            email="test@example.com",
            display_name="Test User",
            password="password123",
            git_name="Test User",
            git_email="test@example.com"
        )
        user = await auth_service.create_user(user_create)
        
        # Create multiple API keys
        for i in range(3):
            api_key_create = APIKeyCreate(
                name=f"API Key {i}",
                scopes=["read"]
            )
            await auth_service.create_api_key(user.id, api_key_create)
        
        # List keys
        keys = await auth_service.list_user_api_keys(user.id)
        
        assert len(keys) == 3
        assert all(key.user_id == user.id for key in keys)
    
    @pytest.mark.asyncio
    async def test_authenticate_api_key(self, auth_service):
        """Test authenticating with an API key."""
        # Create user
        user_create = UserCreate(
            email="test@example.com",
            display_name="Test User",
            password="password123",
            git_name="Test User",
            git_email="test@example.com"
        )
        user = await auth_service.create_user(user_create)
        
        # Create API key
        api_key_create = APIKeyCreate(
            name="Test API Key",
            scopes=["read"]
        )
        api_key, plaintext_key = await auth_service.create_api_key(
            user.id,
            api_key_create
        )
        
        # Authenticate
        result = await auth_service.authenticate_api_key(plaintext_key)
        
        assert result is not None
        authenticated_user, authenticated_key = result
        assert authenticated_user.id == user.id
        assert authenticated_key.id == api_key.id
    
    @pytest.mark.asyncio
    async def test_authenticate_invalid_api_key(self, auth_service):
        """Test authenticating with invalid API key."""
        result = await auth_service.authenticate_api_key("invalid_key")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_revoke_api_key(self, auth_service):
        """Test revoking an API key."""
        # Create user
        user_create = UserCreate(
            email="test@example.com",
            display_name="Test User",
            password="password123",
            git_name="Test User",
            git_email="test@example.com"
        )
        user = await auth_service.create_user(user_create)
        
        # Create API key
        api_key_create = APIKeyCreate(
            name="Test API Key",
            scopes=["read"]
        )
        api_key, plaintext_key = await auth_service.create_api_key(
            user.id,
            api_key_create
        )
        
        # Revoke key
        success = await auth_service.revoke_api_key(api_key.id)
        assert success is True
        
        # Verify key is gone
        retrieved = await auth_service.get_api_key(api_key.id)
        assert retrieved is None
        
        # Verify it's removed from user's list
        keys = await auth_service.list_user_api_keys(user.id)
        assert len(keys) == 0
    
    @pytest.mark.asyncio
    async def test_update_user(self, auth_service):
        """Test updating user fields."""
        # Create user
        user_create = UserCreate(
            email="test@example.com",
            display_name="Test User",
            password="password123",
            git_name="Test User",
            git_email="test@example.com"
        )
        user = await auth_service.create_user(user_create)
        
        # Update user
        updated = await auth_service.update_user(
            user.id,
            display_name="Updated Name",
            default_model="gpt-4"
        )
        
        assert updated is not None
        assert updated.display_name == "Updated Name"
        assert updated.default_model == "gpt-4"
        assert updated.email == user.email  # Unchanged
