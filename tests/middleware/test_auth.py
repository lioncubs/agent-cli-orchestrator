"""Tests for authentication middleware."""

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.api.middleware.auth import AuthMiddleware, get_current_user
from src.auth.service import AuthService
from src.auth.models import User, APIKey
from src.session.models import GitIdentity


@pytest.fixture
def mock_auth_service():
    """Create a mock authentication service."""
    service = AsyncMock(spec=AuthService)
    return service


@pytest.fixture
def test_app(mock_auth_service):
    """Create a test FastAPI app with auth middleware."""
    app = FastAPI()
    
    # Add auth middleware
    app.add_middleware(
        AuthMiddleware,
        auth_service=mock_auth_service,
        exclude_paths=["/public", "/health"],
        require_auth=True
    )
    
    # Test endpoints
    @app.get("/public")
    async def public_endpoint():
        return {"message": "public"}
    
    @app.get("/protected")
    async def protected_endpoint(request: Request):
        user = get_current_user(request)
        return {"message": "protected", "user": user.email}
    
    @app.get("/health")
    async def health_check():
        return {"status": "ok"}
    
    return app, mock_auth_service


class TestAuthMiddleware:
    """Tests for authentication middleware."""
    
    def test_public_endpoint_no_auth(self, test_app):
        """Test that public endpoints don't require auth."""
        app, _ = test_app
        client = TestClient(app)
        
        response = client.get("/public")
        assert response.status_code == 200
        assert response.json()["message"] == "public"
    
    def test_health_endpoint_excluded(self, test_app):
        """Test that health endpoints are excluded."""
        app, _ = test_app
        client = TestClient(app)
        
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
    
    def test_protected_endpoint_missing_auth(self, test_app):
        """Test protected endpoint without auth header."""
        app, _ = test_app
        client = TestClient(app)
        
        response = client.get("/protected")
        assert response.status_code == 401
        assert "Missing authentication credentials" in response.json()["detail"]
    
    def test_protected_endpoint_invalid_format(self, test_app):
        """Test protected endpoint with invalid auth header format."""
        app, _ = test_app
        client = TestClient(app)
        
        response = client.get(
            "/protected",
            headers={"Authorization": "InvalidFormat"}
        )
        assert response.status_code == 401
        assert "Invalid authentication credentials format" in response.json()["detail"]
    
    def test_protected_endpoint_unsupported_scheme(self, test_app):
        """Test protected endpoint with unsupported auth scheme."""
        app, _ = test_app
        client = TestClient(app)
        
        response = client.get(
            "/protected",
            headers={"Authorization": "Basic dXNlcjpwYXNz"}
        )
        assert response.status_code == 401
        assert "Unsupported authentication scheme" in response.json()["detail"]
    
    def test_protected_endpoint_invalid_key(self, test_app):
        """Test protected endpoint with invalid API key."""
        app, mock_service = test_app
        client = TestClient(app)
        
        # Mock authenticate_api_key to return None (invalid key)
        mock_service.authenticate_api_key.return_value = None
        
        response = client.get(
            "/protected",
            headers={"Authorization": "Bearer invalid_key_123"}
        )
        assert response.status_code == 401
        assert "Invalid or expired API key" in response.json()["detail"]
    
    def test_protected_endpoint_valid_key(self, test_app):
        """Test protected endpoint with valid API key."""
        app, mock_service = test_app
        client = TestClient(app)
        
        # Create mock user and API key
        user = User(
            id=uuid4(),
            email="test@example.com",
            display_name="Test User",
            password_hash="hashed",
            git_identity=GitIdentity(name="Test", email="test@example.com")
        )
        
        api_key = APIKey(
            id=uuid4(),
            key_hash="hash",
            user_id=user.id,
            name="Test Key",
            scopes=["read", "write"]
        )
        
        # Mock authenticate_api_key to return user and key
        mock_service.authenticate_api_key.return_value = (user, api_key)
        
        response = client.get(
            "/protected",
            headers={"Authorization": "Bearer valid_key_abc"}
        )
        assert response.status_code == 200
        assert response.json()["message"] == "protected"
        assert response.json()["user"] == "test@example.com"
    
    def test_auth_with_apikey_scheme(self, test_app):
        """Test authentication with 'ApiKey' scheme."""
        app, mock_service = test_app
        client = TestClient(app)
        
        user = User(
            id=uuid4(),
            email="user@example.com",
            display_name="User",
            password_hash="hashed",
            git_identity=GitIdentity(name="User", email="user@example.com")
        )
        
        api_key = APIKey(
            id=uuid4(),
            key_hash="hash",
            user_id=user.id,
            name="Key",
            scopes=["read"]
        )
        
        mock_service.authenticate_api_key.return_value = (user, api_key)
        
        response = client.get(
            "/protected",
            headers={"Authorization": "ApiKey my_key_123"}
        )
        assert response.status_code == 200
    
    def test_get_current_user_not_authenticated(self):
        """Test get_current_user when not authenticated."""
        request = MagicMock(spec=Request)
        request.state = MagicMock()
        delattr(request.state, "user")  # Remove user attribute
        
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(request)
        
        assert exc_info.value.status_code == 401


@pytest.fixture
def test_app_auth_optional(mock_auth_service):
    """Create a test app with optional authentication."""
    app = FastAPI()
    
    app.add_middleware(
        AuthMiddleware,
        auth_service=mock_auth_service,
        require_auth=False  # Auth not required
    )
    
    @app.get("/optional")
    async def optional_auth():
        return {"message": "ok"}
    
    return app, mock_auth_service


class TestAuthMiddlewareOptional:
    """Tests for optional authentication."""
    
    def test_optional_auth_without_header(self, test_app_auth_optional):
        """Test endpoint without auth when auth is optional."""
        app, _ = test_app_auth_optional
        client = TestClient(app)
        
        response = client.get("/optional")
        assert response.status_code == 200
        assert response.json()["message"] == "ok"
