# Security Hardening Addendum

## Overview

This addendum complements the existing [action-plan.md](action-plan.md) and outlines critical security enhancements that should be implemented before Phase 5 feature development. Security hardening is essential for production deployment and protecting against common web application vulnerabilities.

---

## Phase 4.5: Security Hardening

**Priority**: HIGH  
**Timeline**: 2-3 weeks  
**Prerequisites**: Complete before Phase 5 feature enhancements  
**Dependencies**: Existing Phase 4 (CI/CD Setup) can run in parallel

### Strategic Importance

Security hardening transforms the Agent CLI Orchestrator from a development tool into a production-ready service. This phase addresses:
- OWASP Top 10 vulnerabilities
- Container security best practices
- Data protection and secrets management
- Infrastructure resilience

---

## Task 4.5.1: HTTPS/TLS Configuration

**Priority**: CRITICAL  
**Estimated Time**: 3-4 hours  
**Impact**: Protects data in transit, prevents MITM attacks

### Objectives
- Enable encrypted communications between clients and server
- Automate certificate management
- Enforce HTTPS in production environments

### Implementation Steps

#### 1. Configure Uvicorn with SSL/TLS

Update `main.py` or create a production startup script:

```python
import ssl
from pathlib import Path

def create_ssl_context():
    """Create SSL context for HTTPS."""
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(
        certfile="/etc/ssl/certs/fullchain.pem",
        keyfile="/etc/ssl/private/privkey.pem"
    )
    # Security hardening
    ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
    ssl_context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
    return ssl_context

if __name__ == "__main__":
    import uvicorn
    
    if os.getenv("ENVIRONMENT") == "production":
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=443,
            ssl_keyfile="/etc/ssl/private/privkey.pem",
            ssl_certfile="/etc/ssl/certs/fullchain.pem",
            ssl_version=ssl.PROTOCOL_TLS_SERVER,
            ssl_cert_reqs=ssl.CERT_NONE,
        )
    else:
        uvicorn.run("main:app", host="0.0.0.0", port=8000)
```

#### 2. Let's Encrypt Integration

Create `scripts/setup_letsencrypt.sh`:

```bash
#!/bin/bash
# Let's Encrypt certificate setup for production

DOMAIN="${DOMAIN:-example.com}"
EMAIL="${EMAIL:-admin@example.com}"

# Install certbot
apt-get update
apt-get install -y certbot

# Obtain certificate
certbot certonly --standalone \
    --non-interactive \
    --agree-tos \
    --email "$EMAIL" \
    -d "$DOMAIN"

# Create symlinks for easy access
ln -sf /etc/letsencrypt/live/$DOMAIN/fullchain.pem /etc/ssl/certs/fullchain.pem
ln -sf /etc/letsencrypt/live/$DOMAIN/privkey.pem /etc/ssl/private/privkey.pem
```

#### 3. HTTP to HTTPS Redirect Middleware

Add to `main.py`:

```python
from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if os.getenv("ENVIRONMENT") == "production":
            if request.url.scheme == "http":
                url = request.url.replace(scheme="https")
                return RedirectResponse(url=url, status_code=301)
        return await call_next(request)

# Add to app
app.add_middleware(HTTPSRedirectMiddleware)
```

#### 4. Certificate Auto-Renewal

Create `scripts/renew_certs.sh`:

```bash
#!/bin/bash
# Automatic certificate renewal (run via cron)

certbot renew --quiet --deploy-hook "systemctl reload nginx"

# Add to crontab:
# 0 3 * * * /path/to/renew_certs.sh
```

### Testing
```bash
# Test SSL configuration
openssl s_client -connect localhost:443 -tls1_2

# Verify certificate
curl -vI https://localhost:443

# Test HTTP redirect
curl -I http://localhost:80
```

### Success Criteria
- [ ] HTTPS enabled on production server
- [ ] Valid SSL/TLS certificate installed
- [ ] HTTP requests redirect to HTTPS
- [ ] Auto-renewal configured and tested
- [ ] TLS 1.2+ enforced

---

## Task 4.5.2: Security Headers & CORS

**Priority**: HIGH  
**Estimated Time**: 2 hours  
**Impact**: Prevents XSS, clickjacking, and other client-side attacks

### Objectives
- Implement comprehensive security headers
- Configure proper CORS policies
- Protect against common web vulnerabilities

### Implementation

#### Security Headers Middleware

Create `security_middleware.py`:

```python
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Strict-Transport-Security (HSTS)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
        # Content-Security-Policy (CSP)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        
        # X-Frame-Options
        response.headers["X-Frame-Options"] = "DENY"
        
        # X-Content-Type-Options
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-XSS-Protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer-Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions-Policy
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response

# Add to main.py
from security_middleware import SecurityHeadersMiddleware
app.add_middleware(SecurityHeadersMiddleware)
```

#### CORS Configuration

Update CORS settings in `main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

# Environment-specific CORS configuration
if os.getenv("ENVIRONMENT") == "production":
    allowed_origins = [
        "https://yourdomain.com",
        "https://app.yourdomain.com"
    ]
else:
    allowed_origins = ["http://localhost:3000", "http://localhost:8000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    expose_headers=["Content-Length", "X-Request-ID"],
    max_age=3600,
)
```

### Testing
```bash
# Test security headers
curl -I https://localhost:443

# Test CORS
curl -H "Origin: https://yourdomain.com" \
     -H "Access-Control-Request-Method: POST" \
     -X OPTIONS https://localhost:443/api/endpoint
```

### Success Criteria
- [ ] All security headers present in responses
- [ ] CORS configured for production domains
- [ ] A+ rating on securityheaders.com
- [ ] No console warnings in browser
- [ ] CSP violations logged and monitored

---

## Task 4.5.3: Input Validation & Sanitization

**Priority**: HIGH  
**Estimated Time**: 3 hours  
**Impact**: Prevents injection attacks, path traversal, and malicious input

### Objectives
- Validate all user inputs with Pydantic models
- Sanitize file paths and Git repository inputs
- Implement request size limits
- Validate file uploads

### Implementation

#### 1. Pydantic Models for All Endpoints

Create `models/requests.py`:

```python
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List
import re

class GitOperationRequest(BaseModel):
    """Validated Git operation request."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    repository: str = Field(..., min_length=1, max_length=255)
    branch: Optional[str] = Field(None, max_length=255)
    
    @field_validator('repository')
    @classmethod
    def validate_repository(cls, v: str) -> str:
        # Prevent path traversal
        if '..' in v or v.startswith('/'):
            raise ValueError('Invalid repository name')
        # Allow only alphanumeric, hyphens, underscores
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Repository name contains invalid characters')
        return v
    
    @field_validator('branch')
    @classmethod
    def validate_branch(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        # Git branch name validation
        if not re.match(r'^[a-zA-Z0-9/_-]+$', v):
            raise ValueError('Invalid branch name')
        return v

class CopilotPromptRequest(BaseModel):
    """Validated Copilot prompt request."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    prompt: str = Field(..., min_length=1, max_length=10000)
    repository: Optional[str] = Field(None, max_length=255)
    timeout: Optional[int] = Field(30, ge=1, le=300)
    
    @field_validator('prompt')
    @classmethod
    def validate_prompt(cls, v: str) -> str:
        # Remove potentially dangerous characters
        if any(char in v for char in ['\x00', '\r']):
            raise ValueError('Prompt contains invalid characters')
        return v

class FileUploadRequest(BaseModel):
    """Validated file upload request."""
    filename: str = Field(..., max_length=255)
    content_type: str = Field(..., max_length=100)
    
    @field_validator('filename')
    @classmethod
    def validate_filename(cls, v: str) -> str:
        # Prevent path traversal
        if '..' in v or '/' in v or '\\' in v:
            raise ValueError('Invalid filename')
        # Sanitize filename
        v = re.sub(r'[^\w\s.-]', '', v)
        return v
```

#### 2. Path Traversal Prevention

Create `utils/security.py`:

```python
from pathlib import Path
from typing import Union

def sanitize_path(base_path: Path, user_path: str) -> Path:
    """
    Sanitize and validate file paths to prevent path traversal.
    
    Args:
        base_path: The base directory that files must stay within
        user_path: User-provided path (potentially malicious)
    
    Returns:
        Validated Path object
    
    Raises:
        ValueError: If path traversal is detected
    """
    # Resolve to absolute path
    full_path = (base_path / user_path).resolve()
    
    # Ensure path is within base_path
    try:
        full_path.relative_to(base_path.resolve())
    except ValueError:
        raise ValueError(f"Path traversal detected: {user_path}")
    
    return full_path

# Usage example
def safe_read_file(repository: str, filepath: str) -> str:
    base_path = Path(f"/repositories/{repository}")
    safe_path = sanitize_path(base_path, filepath)
    return safe_path.read_text()
```

#### 3. Request Size Limits

Add to `main.py`:

```python
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_size: int = 10 * 1024 * 1024):  # 10MB default
        super().__init__(app)
        self.max_size = max_size
    
    async def dispatch(self, request: Request, call_next):
        if request.method in ["POST", "PUT", "PATCH"]:
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > self.max_size:
                raise HTTPException(
                    status_code=413,
                    detail=f"Request size exceeds maximum allowed size of {self.max_size} bytes"
                )
        return await call_next(request)

app.add_middleware(RequestSizeLimitMiddleware, max_size=10 * 1024 * 1024)
```

#### 4. File Upload Validation

```python
from fastapi import UploadFile, HTTPException

ALLOWED_EXTENSIONS = {'.txt', '.md', '.json', '.yaml', '.yml', '.py'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

async def validate_upload(file: UploadFile):
    """Validate uploaded file."""
    # Check file extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type {ext} not allowed. Allowed types: {ALLOWED_EXTENSIONS}"
        )
    
    # Check file size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File size exceeds maximum of {MAX_FILE_SIZE} bytes"
        )
    
    # Reset file pointer
    await file.seek(0)
    return True
```

### Testing
```bash
# Test path traversal prevention
curl -X POST http://localhost:8000/api/file \
     -d '{"filepath": "../../../etc/passwd"}'

# Test request size limit
dd if=/dev/zero of=large.txt bs=1M count=20
curl -X POST http://localhost:8000/api/upload \
     -F "file=@large.txt"

# Test invalid input
curl -X POST http://localhost:8000/api/git/checkout \
     -d '{"repository": "../../malicious", "branch": "main"}'
```

### Success Criteria
- [ ] All endpoints use Pydantic models
- [ ] Path traversal attacks blocked
- [ ] Request size limits enforced
- [ ] File uploads validated
- [ ] Input validation tests passing

---

## Task 4.5.4: Secrets Management

**Priority**: CRITICAL  
**Estimated Time**: 2-3 hours  
**Impact**: Protects sensitive credentials and API keys

### Objectives
- Remove hardcoded credentials from code
- Externalize secrets to environment variables
- Support multiple secrets management backends
- Provide migration path for existing deployments

### Implementation

#### 1. Environment Variables

Create `.env.example`:

```bash
# Application Configuration
ENVIRONMENT=development
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000

# Security
SECRET_KEY=your-secret-key-here-change-in-production
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# GitHub Configuration (if using GitHub API)
GITHUB_TOKEN=ghp_your_github_token_here
GITHUB_WEBHOOK_SECRET=your_webhook_secret

# Database (if applicable)
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# SSL/TLS
SSL_CERT_PATH=/etc/ssl/certs/fullchain.pem
SSL_KEY_PATH=/etc/ssl/private/privkey.pem

# External Services
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_REGION=us-east-1
```

Update `.gitignore`:

```gitignore
.env
.env.local
.env.*.local
*.pem
*.key
secrets/
```

#### 2. Configuration Loader with Secrets

Update `config_loader.py`:

```python
import os
from typing import Optional
from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class SecurityConfig(BaseSettings):
    """Security-related configuration from environment."""
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False
    )
    
    secret_key: SecretStr = Field(default="change-me-in-production")
    github_token: Optional[SecretStr] = None
    database_url: Optional[SecretStr] = None
    aws_access_key_id: Optional[SecretStr] = None
    aws_secret_access_key: Optional[SecretStr] = None

# Initialize
security_config = SecurityConfig()

# Usage - secrets are automatically masked in logs
print(security_config.secret_key)  # Outputs: **********
print(security_config.secret_key.get_secret_value())  # Actual value
```

#### 3. AWS Secrets Manager Integration

Create `utils/secrets_manager.py`:

```python
import boto3
import json
from typing import Dict, Any
from functools import lru_cache

class SecretsManager:
    """Abstract secrets manager interface."""
    
    def get_secret(self, key: str) -> str:
        raise NotImplementedError

class AWSSecretsManager(SecretsManager):
    """AWS Secrets Manager integration."""
    
    def __init__(self, region: str = "us-east-1"):
        self.client = boto3.client('secretsmanager', region_name=region)
    
    @lru_cache(maxsize=128)
    def get_secret(self, secret_name: str) -> Dict[str, Any]:
        """Get secret from AWS Secrets Manager with caching."""
        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            return json.loads(response['SecretString'])
        except Exception as e:
            raise ValueError(f"Failed to retrieve secret {secret_name}: {e}")

class VaultSecretsManager(SecretsManager):
    """HashiCorp Vault integration."""
    
    def __init__(self, vault_addr: str, vault_token: str):
        import hvac
        self.client = hvac.Client(url=vault_addr, token=vault_token)
    
    def get_secret(self, path: str) -> Dict[str, Any]:
        """Get secret from Vault."""
        try:
            secret = self.client.secrets.kv.v2.read_secret_version(path=path)
            return secret['data']['data']
        except Exception as e:
            raise ValueError(f"Failed to retrieve secret from {path}: {e}")

# Factory function
def get_secrets_manager() -> SecretsManager:
    """Get appropriate secrets manager based on environment."""
    backend = os.getenv("SECRETS_BACKEND", "env")
    
    if backend == "aws":
        return AWSSecretsManager()
    elif backend == "vault":
        vault_addr = os.getenv("VAULT_ADDR")
        vault_token = os.getenv("VAULT_TOKEN")
        return VaultSecretsManager(vault_addr, vault_token)
    else:
        # Fallback to environment variables
        return None  # Use direct env var access
```

#### 4. Docker Secrets Support

Update `docker-compose.yml`:

```yaml
version: '3.8'

services:
  app:
    build: .
    secrets:
      - github_token
      - secret_key
    environment:
      - GITHUB_TOKEN_FILE=/run/secrets/github_token
      - SECRET_KEY_FILE=/run/secrets/secret_key

secrets:
  github_token:
    file: ./secrets/github_token.txt
  secret_key:
    file: ./secrets/secret_key.txt
```

Helper function:

```python
def load_secret_from_file(env_var_name: str) -> Optional[str]:
    """Load secret from Docker secrets file."""
    file_path = os.getenv(f"{env_var_name}_FILE")
    if file_path and os.path.exists(file_path):
        with open(file_path) as f:
            return f.read().strip()
    return os.getenv(env_var_name)
```

### Testing
```bash
# Test environment variable loading
python -c "from config_loader import security_config; print('Loaded')"

# Test AWS Secrets Manager
python -c "from utils.secrets_manager import get_secrets_manager; sm = get_secrets_manager(); print(sm.get_secret('app/config'))"

# Test Docker secrets
docker-compose up
```

### Success Criteria
- [ ] No hardcoded credentials in code
- [ ] .env.example provided
- [ ] Secrets loaded from environment
- [ ] AWS Secrets Manager integration working
- [ ] Docker secrets support implemented
- [ ] Vault integration documented

---

## Task 4.5.5: Container Security

**Priority**: HIGH  
**Estimated Time**: 2 hours  
**Impact**: Hardens container against attacks, reduces attack surface

### Objectives
- Run containers as non-root user
- Use minimal base images
- Implement multi-stage builds
- Enable read-only filesystem where possible
- Integrate security scanning

### Implementation

#### 1. Secure Dockerfile

Create production `Dockerfile`:

```dockerfile
# Multi-stage build for minimal final image
FROM python:3.12-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.12-slim

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser -u 1000 appuser

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=appuser:appuser . .

# Set up environment
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Create necessary directories with correct permissions
RUN mkdir -p /app/logs /app/data && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 2. Read-Only Filesystem

Update `docker-compose.yml`:

```yaml
version: '3.8'

services:
  app:
    build: .
    read_only: true
    tmpfs:
      - /tmp
      - /app/logs:uid=1000,gid=1000
    volumes:
      - ./data:/app/data:ro
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
```

#### 3. Security Scanning

Create `.github/workflows/security-scan.yml`:

```yaml
name: Container Security Scan

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  trivy-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build image
        run: docker build -t app:latest .
      
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'app:latest'
          format: 'sarif'
          output: 'trivy-results.sarif'
          severity: 'CRITICAL,HIGH'
      
      - name: Upload Trivy results to GitHub Security tab
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'
```

#### 4. Image Scanning Script

Create `scripts/scan_image.sh`:

```bash
#!/bin/bash
# Scan Docker image for vulnerabilities

IMAGE_NAME="${1:-app:latest}"

echo "Scanning $IMAGE_NAME with Trivy..."
trivy image --severity HIGH,CRITICAL "$IMAGE_NAME"

echo "Scanning with Grype..."
grype "$IMAGE_NAME"

echo "Checking for secrets with Trufflehog..."
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    trufflesecurity/trufflehog:latest docker --image "$IMAGE_NAME"
```

### Testing
```bash
# Build and scan image
docker build -t app:latest .
./scripts/scan_image.sh app:latest

# Test non-root user
docker run app:latest whoami  # Should output: appuser

# Test read-only filesystem
docker-compose up
docker exec <container> touch /test  # Should fail
```

### Success Criteria
- [ ] Container runs as non-root user
- [ ] Multi-stage build implemented
- [ ] No HIGH/CRITICAL vulnerabilities in scan
- [ ] Read-only filesystem configured
- [ ] Security scanning in CI/CD
- [ ] Image size optimized

---

## Task 4.5.6: Dependency Security

**Priority**: HIGH  
**Estimated Time**: 1 hour  
**Impact**: Prevents supply chain attacks and vulnerable dependencies

### Objectives
- Automate dependency vulnerability scanning
- Keep dependencies up to date
- Pin specific versions for reproducibility
- Monitor for security advisories

### Implementation

#### 1. Dependabot Configuration

Create `.github/dependabot.yml`:

```yaml
version: 2
updates:
  # Python dependencies
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 10
    reviewers:
      - "security-team"
    labels:
      - "dependencies"
      - "security"
    commit-message:
      prefix: "deps"
    # Security updates only
    allow:
      - dependency-type: "all"
    
  # Docker dependencies
  - package-ecosystem: "docker"
    directory: "/"
    schedule:
      interval: "weekly"
    
  # GitHub Actions
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

#### 2. Safety Check Integration

Create `.github/workflows/dependency-check.yml`:

```yaml
name: Dependency Security Check

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday

jobs:
  safety-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install Safety
        run: pip install safety
      
      - name: Check dependencies with Safety
        run: safety check --json --continue-on-error
        continue-on-error: true
      
      - name: Install and run pip-audit
        run: |
          pip install pip-audit
          pip-audit --desc
  
  snyk-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run Snyk to check for vulnerabilities
        uses: snyk/actions/python@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          args: --severity-threshold=high
```

#### 3. Pin Dependency Versions

Update `requirements.txt`:

```text
# Web Framework
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6

# Async Support
aiofiles==23.2.1

# Configuration
pyyaml==6.0.1
python-dotenv==1.0.0
pydantic==2.5.3
pydantic-settings==2.1.0

# Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
bcrypt==4.1.2

# Testing
pytest==7.4.4
pytest-asyncio==0.23.3
pytest-cov==4.1.0
httpx==0.26.0

# Security Scanning
safety==3.0.1
```

#### 4. Local Security Check Script

Create `scripts/check_dependencies.sh`:

```bash
#!/bin/bash
# Check dependencies for known vulnerabilities

set -e

echo "🔍 Checking dependencies for security vulnerabilities..."

echo "📦 Checking with Safety..."
pip install safety
safety check --json || true

echo "🔎 Checking with pip-audit..."
pip install pip-audit
pip-audit --desc || true

echo "📊 Checking for outdated packages..."
pip list --outdated

echo "✅ Dependency check complete!"
```

### Testing
```bash
# Run security checks locally
./scripts/check_dependencies.sh

# Test Dependabot (simulated)
# Check .github/dependabot.yml is valid
gh api repos/:owner/:repo/dependabot/secrets

# Verify pinned versions
pip-compile --generate-hashes requirements.in
```

### Success Criteria
- [ ] Dependabot configured and active
- [ ] Safety checks in CI/CD pipeline
- [ ] All dependencies pinned to specific versions
- [ ] No HIGH/CRITICAL vulnerabilities
- [ ] Weekly automated scans running
- [ ] Security alerts configured

---

## Task 4.5.7: Rate Limiting & DDoS Protection

**Priority**: MEDIUM  
**Estimated Time**: 2 hours  
**Impact**: Prevents abuse, ensures service availability

### Objectives
- Implement per-IP rate limiting
- Configure per-endpoint limits
- Add configurable rate limit rules
- Provide bypass for authenticated users

### Implementation

#### 1. Install slowapi

Update `requirements.txt`:

```text
slowapi==0.1.9
```

#### 2. Rate Limiting Middleware

Create `middleware/rate_limit.py`:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from typing import Callable

# Initialize limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute", "1000/hour"]
)

# Custom key function for authenticated users
def get_api_key(request: Request) -> str:
    """Get rate limit key from API key or IP address."""
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"apikey:{api_key}"
    return get_remote_address(request)

# Authenticated limiter with higher limits
auth_limiter = Limiter(
    key_func=get_api_key,
    default_limits=["1000/minute", "10000/hour"]
)
```

Update `main.py`:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from middleware.rate_limit import limiter, auth_limiter

# Add to FastAPI app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Apply to endpoints
@app.get("/api/status")
@limiter.limit("10/minute")
async def status(request: Request):
    return {"status": "ok"}

@app.post("/api/copilot/prompt")
@limiter.limit("20/minute")  # More restrictive for expensive operations
async def copilot_prompt(request: Request, prompt: str):
    # Handle Copilot request
    pass

@app.post("/api/git/checkout")
@auth_limiter.limit("100/minute")  # Higher limit for authenticated
async def git_checkout(request: Request, data: GitCheckoutRequest):
    # Handle Git operation
    pass
```

#### 3. Configurable Rate Limits

Update `config.yaml`:

```yaml
rate_limits:
  enabled: true
  
  # Default limits
  default:
    per_minute: 100
    per_hour: 1000
  
  # Authenticated user limits
  authenticated:
    per_minute: 1000
    per_hour: 10000
  
  # Per-endpoint limits
  endpoints:
    "/api/copilot/prompt":
      per_minute: 20
      per_hour: 200
    "/api/git/*":
      per_minute: 50
      per_hour: 500
    "/api/status":
      per_minute: 100
      per_hour: 1000
  
  # Whitelist IPs (no rate limiting)
  whitelist:
    - "127.0.0.1"
    - "10.0.0.0/8"
```

#### 4. Custom Rate Limit Response

```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom rate limit exceeded response."""
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "message": f"Too many requests. Please try again later.",
            "retry_after": exc.detail,
        },
        headers={
            "Retry-After": str(exc.detail),
            "X-RateLimit-Limit": request.state.view_rate_limit,
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(exc.detail),
        }
    )
```

### Testing
```bash
# Test rate limiting
for i in {1..150}; do
  curl http://localhost:8000/api/status
done

# Test with API key
for i in {1..150}; do
  curl -H "X-API-Key: test-key" http://localhost:8000/api/status
done

# Check rate limit headers
curl -I http://localhost:8000/api/status
```

### Success Criteria
- [ ] Rate limiting active on all endpoints
- [ ] Per-IP limits enforced
- [ ] Per-endpoint limits configured
- [ ] Authenticated users have higher limits
- [ ] Rate limit headers included in responses
- [ ] Whitelist functionality working

---

## Task 4.5.8: Audit Logging & Monitoring

**Priority**: MEDIUM  
**Estimated Time**: 2 hours  
**Impact**: Enables security incident detection and forensics

### Objectives
- Enhanced activity logging with security events
- Track failed authentication attempts
- Detect suspicious activity patterns
- Integration with external logging services

### Implementation

#### 1. Enhanced Activity Logger

Update `activity_log.py`:

```python
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from enum import Enum
import json

class EventSeverity(Enum):
    """Security event severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class SecurityEventType(Enum):
    """Security event types."""
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INVALID_INPUT = "invalid_input"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_ACCESS = "data_access"
    CONFIG_CHANGE = "config_change"

class AuditLogger:
    """Enhanced audit logger with security event tracking."""
    
    def __init__(self):
        self.logger = logging.getLogger("security_audit")
        self.logger.setLevel(logging.INFO)
        
        # File handler for security events
        handler = logging.FileHandler("logs/security_audit.log")
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def log_event(
        self,
        event_type: SecurityEventType,
        severity: EventSeverity,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None,
    ):
        """Log security event with structured data."""
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type.value,
            "severity": severity.value,
            "message": message,
            "user_id": user_id,
            "ip_address": ip_address,
            "request_id": request_id,
            "metadata": metadata or {},
        }
        
        log_level = getattr(logging, severity.value.upper())
        self.logger.log(log_level, json.dumps(event))
        
        # Alert on critical events
        if severity == EventSeverity.CRITICAL:
            self._send_alert(event)
    
    def log_auth_failure(self, username: str, ip_address: str, reason: str):
        """Log failed authentication attempt."""
        self.log_event(
            event_type=SecurityEventType.AUTH_FAILURE,
            severity=EventSeverity.WARNING,
            message=f"Failed authentication attempt for user: {username}",
            metadata={"username": username, "reason": reason},
            ip_address=ip_address,
        )
    
    def log_suspicious_activity(
        self, 
        activity: str, 
        ip_address: str, 
        details: Dict[str, Any]
    ):
        """Log suspicious activity pattern."""
        self.log_event(
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
            severity=EventSeverity.ERROR,
            message=f"Suspicious activity detected: {activity}",
            metadata=details,
            ip_address=ip_address,
        )
    
    def _send_alert(self, event: Dict[str, Any]):
        """Send alert for critical events (implement notification logic)."""
        # TODO: Integrate with PagerDuty, Slack, email, etc.
        pass

# Initialize global audit logger
audit_logger = AuditLogger()
```

#### 2. Request Logging Middleware

Create `middleware/audit_middleware.py`:

```python
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from activity_log import audit_logger, SecurityEventType, EventSeverity
import uuid
import time

class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Get client IP
        client_ip = request.client.host
        
        # Log request
        start_time = time.time()
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            # Log successful request
            audit_logger.log_event(
                event_type=SecurityEventType.DATA_ACCESS,
                severity=EventSeverity.INFO,
                message=f"{request.method} {request.url.path}",
                metadata={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration * 1000, 2),
                },
                ip_address=client_ip,
                request_id=request_id,
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            return response
            
        except Exception as e:
            # Log error
            audit_logger.log_event(
                event_type=SecurityEventType.ERROR,
                severity=EventSeverity.ERROR,
                message=f"Request failed: {str(e)}",
                metadata={
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                },
                ip_address=client_ip,
                request_id=request_id,
            )
            raise

# Add to main.py
from middleware.audit_middleware import AuditMiddleware
app.add_middleware(AuditMiddleware)
```

#### 3. CloudWatch Integration (Optional)

Create `utils/cloudwatch_logger.py`:

```python
import boto3
from datetime import datetime
from typing import Dict, Any

class CloudWatchLogger:
    """Send logs to AWS CloudWatch."""
    
    def __init__(self, log_group: str, log_stream: str):
        self.client = boto3.client('logs')
        self.log_group = log_group
        self.log_stream = log_stream
        
    def send_log(self, message: str, metadata: Dict[str, Any]):
        """Send log event to CloudWatch."""
        try:
            self.client.put_log_events(
                logGroupName=self.log_group,
                logStreamName=self.log_stream,
                logEvents=[
                    {
                        'timestamp': int(datetime.now().timestamp() * 1000),
                        'message': json.dumps({
                            'message': message,
                            **metadata
                        })
                    }
                ]
            )
        except Exception as e:
            logging.error(f"Failed to send log to CloudWatch: {e}")
```

### Testing
```bash
# Generate test events
curl http://localhost:8000/api/status
curl http://localhost:8000/api/invalid-endpoint

# Check audit logs
tail -f logs/security_audit.log

# Test suspicious activity detection
for i in {1..1000}; do
  curl http://localhost:8000/api/status
done
```

### Success Criteria
- [ ] All API requests logged
- [ ] Security events tracked
- [ ] Failed auth attempts logged
- [ ] Suspicious activity detected
- [ ] Log rotation configured
- [ ] External logging service integration (optional)

---

## Security Checklist

Use this checklist to track security hardening progress:

### SSL/TLS
- [ ] HTTPS enabled in production
- [ ] Valid SSL/TLS certificate installed
- [ ] HTTP to HTTPS redirect configured
- [ ] Certificate auto-renewal setup
- [ ] TLS 1.2+ enforced
- [ ] Strong cipher suites configured

### Headers & CORS
- [ ] HSTS header configured
- [ ] CSP header implemented
- [ ] X-Frame-Options set to DENY
- [ ] X-Content-Type-Options set to nosniff
- [ ] Referrer-Policy configured
- [ ] CORS properly configured for production domains
- [ ] A+ rating on securityheaders.com

### Input Validation
- [ ] Pydantic models for all request bodies
- [ ] Path traversal prevention implemented
- [ ] Git repository input sanitization
- [ ] Request size limits enforced
- [ ] File upload validation active
- [ ] Input validation tests passing

### Secrets Management
- [ ] No hardcoded credentials in code
- [ ] Secrets externalized to environment variables
- [ ] .env.example file created
- [ ] Secrets manager integration (AWS/Vault/Docker)
- [ ] .gitignore updated to exclude secrets

### Container Security
- [ ] Container runs as non-root user
- [ ] Multi-stage Docker build implemented
- [ ] Minimal base image (python:3.12-slim)
- [ ] Read-only filesystem where possible
- [ ] Security scanning integrated
- [ ] No HIGH/CRITICAL vulnerabilities

### Dependencies
- [ ] Dependabot configured
- [ ] Vulnerability scanning in CI/CD
- [ ] All dependencies pinned
- [ ] Weekly automated scans
- [ ] No HIGH/CRITICAL vulnerabilities
- [ ] Security alerts configured

### Rate Limiting
- [ ] Rate limiting enabled on all endpoints
- [ ] Per-IP limits configured
- [ ] Per-endpoint limits set
- [ ] Rate limit headers in responses
- [ ] Whitelist functionality working
- [ ] Load testing completed

### Logging & Monitoring
- [ ] Audit logging operational
- [ ] Security events tracked
- [ ] Failed auth attempts logged
- [ ] Suspicious activity detection
- [ ] Log rotation configured
- [ ] External logging integration (optional)

---

## Success Criteria

### Functional Requirements
1. **HTTPS/TLS**: All production traffic encrypted
2. **Security Headers**: A+ rating on security scanners
3. **Input Validation**: No injection vulnerabilities
4. **Secrets**: All sensitive data externalized
5. **Container**: Running as non-root with security scanning
6. **Dependencies**: No HIGH/CRITICAL vulnerabilities
7. **Rate Limiting**: Protection against abuse
8. **Logging**: Comprehensive audit trail

### Performance Requirements
- Rate limiting does not impact legitimate users
- SSL/TLS handshake < 100ms
- Input validation adds < 10ms latency
- Logging is asynchronous and non-blocking

### Testing Requirements
- All security features have unit tests
- Integration tests for authentication flow
- Load testing with rate limits
- Penetration testing performed
- Security scanning in CI/CD

### Documentation Requirements
- Security configuration documented
- Deployment guide updated
- Incident response plan created
- Security best practices guide

---

## Resources & References

### OWASP
- [OWASP Top 10 2021](https://owasp.org/www-project-top-ten/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)

### FastAPI Security
- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [FastAPI Middleware](https://fastapi.tiangolo.com/tutorial/middleware/)
- [Pydantic Validation](https://docs.pydantic.dev/latest/concepts/validators/)

### Docker Security
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [CIS Docker Benchmark](https://www.cisecurity.org/benchmark/docker)
- [Snyk Docker Security](https://snyk.io/learn/docker-security/)

### SSL/TLS
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)
- [SSL Labs Testing](https://www.ssllabs.com/ssltest/)

### Tools & Services
- [Trivy Container Scanner](https://github.com/aquasecurity/trivy)
- [Safety Python Dependency Checker](https://github.com/pyupio/safety)
- [Snyk Vulnerability Database](https://snyk.io/vuln/)
- [Security Headers Scanner](https://securityheaders.com/)

### Standards & Compliance
- [PCI DSS](https://www.pcisecuritystandards.org/)
- [SOC 2](https://www.aicpa.org/interestareas/frc/assuranceadvisoryservices/aicpasoc2report.html)
- [ISO 27001](https://www.iso.org/isoiec-27001-information-security.html)

---

## Next Steps

After completing Phase 4.5:

1. **Review** this checklist with the team
2. **Prioritize** tasks based on current security posture
3. **Assign** tasks to team members
4. **Test** each security control thoroughly
5. **Document** security configurations
6. **Monitor** security metrics post-deployment
7. **Schedule** regular security reviews

**Proceed to Phase 5** (Feature Enhancements) only after all critical security items are addressed.
