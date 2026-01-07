"""Tests for authentication API routes."""

import pytest
import tempfile
import shutil
from uuid import uuid4
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.api.routes.auth import router, init_auth_routes


class TestAuthRoutes:
    """Test authentication API routes."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)
    
    @pytest.fixture
    def app(self, temp_dir):
        """Create a FastAPI app with auth routes."""
        app = FastAPI()
        init_auth_routes(storage_dir=temp_dir)
        app.include_router(router)
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        return TestClient(app)
    
    def test_register_user(self, client):
        """Test user registration."""
        response = client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "display_name": "Test User",
                "password": "password123",
                "git_name": "Test User",
                "git_email": "test@example.com"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["display_name"] == "Test User"
        assert "id" in data
    
    
    def test_register_duplicate_user(self, client):
        """Test registering duplicate user."""
        user_data = {
            "email": "test@example.com",
            "display_name": "Test User",
            "password": "password123",
            "git_name": "Test User",
            "git_email": "test@example.com"
        }
        
        # Register first time
        response1 = client.post("/auth/register", json=user_data)
        assert response1.status_code == 200
        
        # Try to register again
        response2 = client.post("/auth/register", json=user_data)
        assert response2.status_code == 400
    
    
    def test_login_success(self, client):
        """Test successful login."""
        # Register user first
        client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "display_name": "Test User",
                "password": "password123",
                "git_name": "Test User",
                "git_email": "test@example.com"
            }
        )
        
        # Login
        response = client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert data["user"]["email"] == "test@example.com"
        assert data["message"] == "Login successful"
    
    
    def test_login_wrong_password(self, client):
        """Test login with wrong password."""
        # Register user first
        client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "display_name": "Test User",
                "password": "password123",
                "git_name": "Test User",
                "git_email": "test@example.com"
            }
        )
        
        # Try to login with wrong password
        response = client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrong_password"
            }
        )
        
        assert response.status_code == 401
    
    
    def test_create_api_key(self, client):
        """Test creating an API key."""
        # Register user first
        register_response = client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "display_name": "Test User",
                "password": "password123",
                "git_name": "Test User",
                "git_email": "test@example.com"
            }
        )
        user_id = register_response.json()["id"]
        
        # Create API key
        response = client.post(
            f"/auth/api-keys?user_id={user_id}",
            json={
                "name": "Test API Key",
                "scopes": ["read", "write"]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "api_key" in data
        assert "plaintext_key" in data
        assert data["api_key"]["name"] == "Test API Key"
        assert data["api_key"]["scopes"] == ["read", "write"]
        assert len(data["plaintext_key"]) > 0
    
    
    def test_list_api_keys(self, client):
        """Test listing API keys."""
        # Register user first
        register_response = client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "display_name": "Test User",
                "password": "password123",
                "git_name": "Test User",
                "git_email": "test@example.com"
            }
        )
        user_id = register_response.json()["id"]
        
        # Create API keys
        for i in range(3):
            client.post(
                f"/auth/api-keys?user_id={user_id}",
                json={
                    "name": f"API Key {i}",
                    "scopes": ["read"]
                }
            )
        
        # List API keys
        response = client.get(f"/auth/api-keys?user_id={user_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
    
    
    def test_revoke_api_key(self, client):
        """Test revoking an API key."""
        # Register user first
        register_response = client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "display_name": "Test User",
                "password": "password123",
                "git_name": "Test User",
                "git_email": "test@example.com"
            }
        )
        user_id = register_response.json()["id"]
        
        # Create API key
        create_response = client.post(
            f"/auth/api-keys?user_id={user_id}",
            json={
                "name": "Test API Key",
                "scopes": ["read"]
            }
        )
        api_key_id = create_response.json()["api_key"]["id"]
        
        # Revoke API key
        response = client.delete(f"/auth/api-keys/{api_key_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    
    def test_get_current_user(self, client):
        """Test getting current user."""
        # Register user first
        register_response = client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "display_name": "Test User",
                "password": "password123",
                "git_name": "Test User",
                "git_email": "test@example.com"
            }
        )
        user_id = register_response.json()["id"]
        
        # Get user
        response = client.get(f"/auth/me?user_id={user_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["email"] == "test@example.com"
    
    
    def test_update_current_user(self, client):
        """Test updating current user."""
        # Register user first
        register_response = client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "display_name": "Test User",
                "password": "password123",
                "git_name": "Test User",
                "git_email": "test@example.com"
            }
        )
        user_id = register_response.json()["id"]
        
        # Update user
        response = client.put(
            f"/auth/me?user_id={user_id}",
            json={
                "display_name": "Updated Name",
                "default_model": "gpt-4"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == "Updated Name"
        assert data["default_model"] == "gpt-4"
    
    
    def test_create_credential(self, client):
        """Test creating a Git credential."""
        # Register user first
        register_response = client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "display_name": "Test User",
                "password": "password123",
                "git_name": "Test User",
                "git_email": "test@example.com"
            }
        )
        user_id = register_response.json()["id"]
        
        # Create credential
        response = client.post(
            f"/auth/credentials?user_id={user_id}",
            json={
                "name": "GitHub Token",
                "credential_type": "https_token",
                "credential_value": "ghp_test_token_12345",
                "remote_url": "https://github.com/user/repo.git"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "GitHub Token"
        assert data["credential_type"] == "https_token"
        assert "id" in data
        # Credential value should not be in response
        assert "encrypted_value" not in data
        assert "credential_value" not in data
    
    
    def test_list_credentials(self, client):
        """Test listing Git credentials."""
        # Register user first
        register_response = client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "display_name": "Test User",
                "password": "password123",
                "git_name": "Test User",
                "git_email": "test@example.com"
            }
        )
        user_id = register_response.json()["id"]
        
        # Create credentials
        for i in range(2):
            client.post(
                f"/auth/credentials?user_id={user_id}",
                json={
                    "name": f"Credential {i}",
                    "credential_type": "https_token",
                    "credential_value": f"token_{i}"
                }
            )
        
        # List credentials
        response = client.get(f"/auth/credentials?user_id={user_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
    
    
    def test_delete_credential(self, client):
        """Test deleting a Git credential."""
        # Register user first
        register_response = client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "display_name": "Test User",
                "password": "password123",
                "git_name": "Test User",
                "git_email": "test@example.com"
            }
        )
        user_id = register_response.json()["id"]
        
        # Create credential
        create_response = client.post(
            f"/auth/credentials?user_id={user_id}",
            json={
                "name": "Test Credential",
                "credential_type": "https_token",
                "credential_value": "test_token"
            }
        )
        credential_id = create_response.json()["id"]
        
        # Delete credential
        response = client.delete(
            f"/auth/credentials/{credential_id}?user_id={user_id}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
