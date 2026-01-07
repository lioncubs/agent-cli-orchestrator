"""Tests for rate limiting middleware."""

import pytest
import time
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.middleware.rate_limit import RateLimitMiddleware


@pytest.fixture
def test_app():
    """Create a test FastAPI app with rate limiting."""
    app = FastAPI()
    
    # Add rate limiting with low limits for testing
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=5,
        burst=3,
        exclude_paths=["/health"]
    )
    
    @app.get("/api/test")
    async def test_endpoint():
        return {"message": "ok"}
    
    @app.get("/health")
    async def health_check():
        return {"status": "ok"}
    
    return app


class TestRateLimitMiddleware:
    """Tests for rate limiting middleware."""
    
    def test_excluded_path_no_limit(self, test_app):
        """Test that excluded paths don't have rate limits."""
        client = TestClient(test_app)
        
        # Make many requests to excluded path
        for _ in range(10):
            response = client.get("/health")
            assert response.status_code == 200
    
    def test_rate_limit_headers(self, test_app):
        """Test that rate limit headers are added."""
        client = TestClient(test_app)
        
        response = client.get("/api/test")
        assert response.status_code == 200
        
        # Check headers
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
        
        assert response.headers["X-RateLimit-Limit"] == "5"
    
    def test_burst_limit_enforcement(self, test_app):
        """Test that burst limit is enforced."""
        client = TestClient(test_app)
        
        # Burst limit is 3, so 4th request should be blocked
        for i in range(3):
            response = client.get("/api/test")
            assert response.status_code == 200, f"Request {i+1} should succeed"
        
        # 4th request should be rate limited
        response = client.get("/api/test")
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["detail"]
        assert "Retry-After" in response.headers
    
    def test_rate_limit_per_minute(self, test_app):
        """Test that per-minute limit is enforced."""
        client = TestClient(test_app)
        
        # Make requests up to the limit
        for i in range(5):
            response = client.get("/api/test")
            # First 3 succeed (within burst), then need delays
            if i < 3:
                assert response.status_code == 200
            else:
                # These might fail due to burst limit
                pass
            time.sleep(0.2)  # Small delay to avoid burst limit
        
        # Next request should be rate limited
        response = client.get("/api/test")
        assert response.status_code == 429
    
    def test_rate_limit_response_format(self, test_app):
        """Test rate limit response format."""
        client = TestClient(test_app)
        
        # Exceed burst limit
        for _ in range(4):
            client.get("/api/test")
        
        response = client.get("/api/test")
        assert response.status_code == 429
        
        data = response.json()
        assert data["error"] == "rate_limit_exceeded"
        assert "limit" in data
        assert "reset_at" in data
        
        # Check headers
        assert response.headers["X-RateLimit-Remaining"] == "0"
    
    def test_rate_limit_decreasing_remaining(self, test_app):
        """Test that remaining count decreases with requests."""
        client = TestClient(test_app)
        
        # First request
        response = client.get("/api/test")
        remaining1 = int(response.headers["X-RateLimit-Remaining"])
        
        time.sleep(0.1)
        
        # Second request
        response = client.get("/api/test")
        remaining2 = int(response.headers["X-RateLimit-Remaining"])
        
        # Remaining should decrease
        assert remaining2 < remaining1


@pytest.fixture
def test_app_custom_limits():
    """Create a test app with custom rate limits."""
    app = FastAPI()
    
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=10,
        burst=5
    )
    
    @app.get("/api/test")
    async def test_endpoint():
        return {"message": "ok"}
    
    return app


class TestRateLimitCustomConfiguration:
    """Tests for custom rate limit configuration."""
    
    def test_custom_limits(self, test_app_custom_limits):
        """Test that custom limits are respected."""
        client = TestClient(test_app_custom_limits)
        
        response = client.get("/api/test")
        assert response.status_code == 200
        
        # Check custom limit
        assert response.headers["X-RateLimit-Limit"] == "10"
