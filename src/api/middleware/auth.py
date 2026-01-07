"""Authentication middleware for validating API keys and user tokens."""

from typing import Optional, Callable
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging

from src.auth.service import AuthService
from src.storage.yaml_backend import YAMLBackend

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce authentication on API endpoints.
    
    Extracts and validates API keys from the Authorization header.
    Injects authenticated user into request state.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        auth_service: AuthService,
        exclude_paths: Optional[list[str]] = None,
        require_auth: bool = True
    ):
        """
        Initialize authentication middleware.
        
        Args:
            app: The ASGI application
            auth_service: Authentication service for key validation
            exclude_paths: List of path prefixes to exclude from auth
            require_auth: Whether to require authentication (can be disabled for dev)
        """
        super().__init__(app)
        self.auth_service = auth_service
        self.require_auth = require_auth
        
        # Default excluded paths (health checks, docs, etc.)
        self.exclude_paths = exclude_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/_health",
        ]
    
    async def dispatch(self, request: Request, call_next: Callable):
        """
        Process each request through authentication.
        
        Args:
            request: The incoming request
            call_next: Next middleware/route handler
            
        Returns:
            Response from the next handler or authentication error
        """
        # Check if path is excluded
        path = request.url.path
        if any(path.startswith(excluded) for excluded in self.exclude_paths):
            return await call_next(request)
        
        # If auth is not required, continue without validation
        if not self.require_auth:
            return await call_next(request)
        
        # Extract authorization header
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            logger.warning(f"Missing Authorization header for {path}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": "Missing authentication credentials",
                    "error": "unauthorized"
                },
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Parse authorization header
        try:
            scheme, credentials = auth_header.split(" ", 1)
        except ValueError:
            logger.warning(f"Invalid Authorization header format for {path}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": "Invalid authentication credentials format",
                    "error": "unauthorized"
                },
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Validate scheme
        if scheme.lower() not in ["bearer", "apikey"]:
            logger.warning(f"Unsupported auth scheme '{scheme}' for {path}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": f"Unsupported authentication scheme: {scheme}",
                    "error": "unauthorized"
                },
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Authenticate with API key
        try:
            result = await self.auth_service.authenticate_api_key(credentials)
            
            if not result:
                logger.warning(f"Invalid or expired API key for {path}")
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "detail": "Invalid or expired API key",
                        "error": "unauthorized"
                    },
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            user, api_key = result
            
            # Inject user and API key into request state
            request.state.user = user
            request.state.api_key = api_key
            
            logger.debug(f"Authenticated user {user.email} for {path}")
            
        except Exception as e:
            logger.error(f"Authentication error for {path}: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": "Authentication service error",
                    "error": "server_error"
                }
            )
        
        # Continue to next handler
        return await call_next(request)


def get_current_user(request: Request):
    """
    Dependency to get the current authenticated user from request state.
    
    Args:
        request: The FastAPI request
        
    Returns:
        The authenticated user
        
    Raises:
        HTTPException: If user is not authenticated
    """
    if not hasattr(request.state, "user"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return request.state.user


def get_current_api_key(request: Request):
    """
    Dependency to get the current API key from request state.
    
    Args:
        request: The FastAPI request
        
    Returns:
        The API key used for authentication
        
    Raises:
        HTTPException: If API key is not available
    """
    if not hasattr(request.state, "api_key"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return request.state.api_key
