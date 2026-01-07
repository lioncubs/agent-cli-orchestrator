"""Security headers middleware for CORS, CSP, HSTS, and other security headers."""

from typing import Callable, Optional
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.
    
    Implements:
    - Content Security Policy (CSP)
    - HTTP Strict Transport Security (HSTS)
    - X-Frame-Options
    - X-Content-Type-Options
    - X-XSS-Protection
    - Referrer-Policy
    """
    
    # Default security headers
    DEFAULT_HEADERS = {
        # Prevent MIME type sniffing
        "X-Content-Type-Options": "nosniff",
        
        # Prevent clickjacking
        "X-Frame-Options": "DENY",
        
        # Enable XSS protection in older browsers
        "X-XSS-Protection": "1; mode=block",
        
        # Control referrer information
        "Referrer-Policy": "strict-origin-when-cross-origin",
        
        # Remove server header information
        "X-Powered-By": "",
    }
    
    def __init__(
        self,
        app: ASGIApp,
        enable_hsts: bool = False,
        hsts_max_age: int = 31536000,
        enable_csp: bool = True,
        csp_directives: Optional[dict] = None,
        custom_headers: Optional[dict] = None
    ):
        """
        Initialize security headers middleware.
        
        Args:
            app: The ASGI application
            enable_hsts: Whether to enable HSTS (only for HTTPS)
            hsts_max_age: HSTS max-age in seconds (default: 1 year)
            enable_csp: Whether to enable Content Security Policy
            csp_directives: Custom CSP directives
            custom_headers: Additional custom headers to add
        """
        super().__init__(app)
        self.enable_hsts = enable_hsts
        self.hsts_max_age = hsts_max_age
        self.enable_csp = enable_csp
        
        # Build security headers
        self.headers = self.DEFAULT_HEADERS.copy()
        
        # Add HSTS if enabled
        if self.enable_hsts:
            self.headers["Strict-Transport-Security"] = (
                f"max-age={hsts_max_age}; includeSubDomains; preload"
            )
        
        # Add Content Security Policy
        if self.enable_csp:
            default_csp = {
                "default-src": ["'self'"],
                "script-src": ["'self'", "'unsafe-inline'"],  # Needed for some UI frameworks
                "style-src": ["'self'", "'unsafe-inline'"],   # Needed for some UI frameworks
                "img-src": ["'self'", "data:", "https:"],
                "font-src": ["'self'", "data:"],
                "connect-src": ["'self'"],
                "frame-ancestors": ["'none'"],
                "base-uri": ["'self'"],
                "form-action": ["'self'"],
            }
            
            # Override with custom directives
            if csp_directives:
                default_csp.update(csp_directives)
            
            # Build CSP header value
            csp_value = "; ".join(
                f"{key} {' '.join(values)}"
                for key, values in default_csp.items()
            )
            self.headers["Content-Security-Policy"] = csp_value
        
        # Add custom headers
        if custom_headers:
            self.headers.update(custom_headers)
    
    async def dispatch(self, request: Request, call_next: Callable):
        """
        Add security headers to the response.
        
        Args:
            request: The incoming request
            call_next: Next middleware/route handler
            
        Returns:
            Response with security headers added
        """
        response = await call_next(request)
        
        # Add all security headers to response
        for header, value in self.headers.items():
            if value:  # Only add if value is not empty
                response.headers[header] = value
        
        return response


def setup_cors(
    app,
    allow_origins: list[str] = None,
    allow_credentials: bool = True,
    allow_methods: list[str] = None,
    allow_headers: list[str] = None
):
    """
    Configure CORS middleware for the application.
    
    Args:
        app: The FastAPI application
        allow_origins: List of allowed origins (default: localhost only)
        allow_credentials: Whether to allow credentials
        allow_methods: List of allowed HTTP methods
        allow_headers: List of allowed headers
        
    Returns:
        The app with CORS middleware configured
    """
    # Default to localhost only for security
    if allow_origins is None:
        allow_origins = [
            "http://localhost",
            "http://localhost:8000",
            "http://localhost:3000",  # Common React dev port
            "http://127.0.0.1",
            "http://127.0.0.1:8000",
            "http://127.0.0.1:3000",
        ]
    
    # Default to common methods
    if allow_methods is None:
        allow_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
    
    # Default to common headers including Authorization
    if allow_headers is None:
        allow_headers = [
            "Authorization",
            "Content-Type",
            "Accept",
            "Origin",
            "User-Agent",
            "DNT",
            "Cache-Control",
            "X-Requested-With",
        ]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=allow_credentials,
        allow_methods=allow_methods,
        allow_headers=allow_headers,
        expose_headers=[
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
        ]
    )
    
    logger.info(f"CORS configured with origins: {allow_origins}")
    
    return app
