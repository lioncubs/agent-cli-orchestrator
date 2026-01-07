# Phase 8 Security Hardening - Quick Reference

## Security Configuration

### Enable All Security Features (Production)

```yaml
# config.yaml
server:
  host: "0.0.0.0"  # Listen on all interfaces
  port: 8000
  ssl_enabled: true
  ssl_certfile: "/etc/ssl/certs/server.crt"
  ssl_keyfile: "/etc/ssl/private/server.key"

security:
  auth:
    enabled: true
    require_auth: true  # Enforce authentication
    exclude_paths:
      - "/health"
      - "/docs"
  
  rate_limit:
    enabled: true
    requests_per_minute: 60
    burst: 10
  
  headers:
    enable_hsts: true  # Only with HTTPS
    hsts_max_age: 31536000
    enable_csp: true
  
  cors:
    enabled: true
    allow_origins:
      - "https://yourdomain.com"
      - "https://app.yourdomain.com"
    allow_credentials: true
```

### Development Mode (Less Restrictive)

```yaml
security:
  auth:
    enabled: true
    require_auth: false  # Auth available but not required
    
  rate_limit:
    enabled: false  # Disable for testing
    
  headers:
    enable_hsts: false  # No HTTPS in dev
    enable_csp: true
    
  cors:
    enabled: true
    allow_origins:
      - "http://localhost"
      - "http://localhost:3000"
```

## Using Authentication

### Register a New User

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "display_name": "John Doe",
    "password": "secure_password_123",
    "git_name": "John Doe",
    "git_email": "user@example.com"
  }'
```

### Generate an API Key

```bash
curl -X POST http://localhost:8000/auth/api-keys \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_api_key>" \
  -d '{
    "name": "My API Key",
    "scopes": ["read", "write"]
  }'
```

### Use API Key for Requests

```bash
curl -X GET http://localhost:8000/sessions \
  -H "Authorization: Bearer <your_api_key>"
```

## Security Endpoints

### Health Check
```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "security": {
    "auth_enabled": true,
    "rate_limit_enabled": true,
    "cors_enabled": true,
    "ssl_enabled": false
  },
  "audit_events_count": 42
}
```

### Security Audit Summary
```bash
curl http://localhost:8000/security/summary
```

Response:
```json
{
  "status": "success",
  "summary": {
    "total_events": 42,
    "by_type": {
      "auth_success": 20,
      "auth_failure": 5,
      "rate_limit_exceeded": 2
    },
    "by_severity": {
      "info": 30,
      "warning": 10,
      "error": 2
    },
    "recent_critical": []
  },
  "security_features": {
    "password_hashing": "bcrypt with salt",
    "api_key_hashing": "SHA-256 with salt",
    "rate_limiting": "60 req/min, burst 10",
    "security_headers": "enabled",
    "cors": "configured",
    "input_validation": "enabled",
    "audit_logging": "enabled"
  }
}
```

## Rate Limiting

### Response Headers
All API responses include rate limit headers:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1640995200
```

### Rate Limit Exceeded (429)
```json
{
  "detail": "Rate limit exceeded",
  "error": "rate_limit_exceeded",
  "limit": 60,
  "reset_at": 1640995200
}
```

## Security Headers

All responses include:

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: default-src 'self'; ...
```

With HTTPS enabled:
```
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
```

## TLS/HTTPS Setup

### Generate Self-Signed Certificate (Development)

```bash
openssl req -x509 -newkey rsa:4096 -nodes \
  -out server.crt -keyout server.key -days 365 \
  -subj "/CN=localhost"
```

### Use Let's Encrypt (Production)

```bash
# Install certbot
sudo apt-get install certbot

# Generate certificate
sudo certbot certonly --standalone -d yourdomain.com

# Configure in config.yaml
ssl_certfile: "/etc/letsencrypt/live/yourdomain.com/fullchain.pem"
ssl_keyfile: "/etc/letsencrypt/live/yourdomain.com/privkey.pem"
```

### Auto-Renewal

```bash
# Add to crontab
0 0 * * * certbot renew --quiet && systemctl restart orchestrator
```

## Input Validation

All user inputs are validated and sanitized:

- **Branch Names**: Only alphanumeric, dash, underscore, slash
- **Paths**: No `..` or absolute paths
- **Commands**: No shell metacharacters
- **Emails**: RFC-compliant format
- **UUIDs**: Standard UUID format

Invalid input returns 400 Bad Request.

## Audit Logging

All security events are logged:

### Event Types
- `auth_success`, `auth_failure` - Authentication events
- `auth_invalid_key`, `auth_expired_key` - API key issues
- `user_created`, `user_updated`, `user_deleted` - User management
- `api_key_created`, `api_key_revoked` - API key lifecycle
- `permission_denied` - Authorization failures
- `rate_limit_exceeded` - Rate limiting
- `suspicious_activity` - Security violations

### Severity Levels
- **info**: Normal operations (successful auth, key usage)
- **warning**: Potential issues (failed auth, rate limits)
- **error**: Security violations (invalid input, suspicious activity)
- **critical**: Severe security issues

## Migrating from Phase 7

### Password Hashes
Existing SHA-256 password hashes need to be re-hashed:

1. **Option A**: Users re-authenticate (automatic re-hashing)
2. **Option B**: Run migration script (to be implemented)

### API Keys
API keys are backward compatible:
- Legacy unsalted keys still work
- New keys use salted hashing
- Regenerate keys for better security

### No Breaking Changes
All API endpoints remain the same.

## Environment Variables

```bash
# Optional: Custom encryption key for credentials
export ORCHESTRATOR_ENCRYPTION_KEY="your-32-byte-base64-key"

# Optional: Override configuration
export ORCHESTRATOR_CONFIG_PATH="/etc/orchestrator/config.yaml"
```

## Troubleshooting

### Authentication Issues

**Problem**: "Missing authentication credentials"
```bash
# Solution: Include Authorization header
curl -H "Authorization: Bearer <your_key>" ...
```

**Problem**: "Invalid or expired API key"
```bash
# Solution: Check key is correct and not expired
# Generate new key via /auth/api-keys
```

### Rate Limiting

**Problem**: "Rate limit exceeded"
```bash
# Solution: Wait for reset time or reduce request rate
# Check X-RateLimit-Reset header for when limit resets
```

### HTTPS/TLS

**Problem**: Certificate errors
```bash
# Development: Use self-signed cert
# Production: Use Let's Encrypt or proper CA cert
```

## Performance Impact

### Bcrypt Password Hashing
- ~100ms per hash operation
- Only during authentication (not in hot path)
- Configurable work factor (default: 12 rounds)

### Rate Limiting
- O(1) per request
- Negligible memory overhead
- Automatic cleanup every 5 minutes

### Security Headers
- Minimal overhead (<1ms)
- Added to all responses

### Authentication Middleware
- O(n) key lookup (n = number of keys)
- Future optimization: hash-based index for O(1)

## Security Best Practices

1. **Always use HTTPS in production** - Enable SSL/TLS
2. **Use strong passwords** - Minimum 12 characters
3. **Rotate API keys regularly** - Every 90 days
4. **Monitor audit logs** - Check for suspicious activity
5. **Keep rate limits reasonable** - Balance security and UX
6. **Restrict CORS origins** - Only allow trusted domains
7. **Update dependencies** - Keep bcrypt and libraries current
8. **Backup encryption keys** - Store securely
9. **Enable HSTS** - Force HTTPS usage
10. **Review security summary** - Regular security audits

## Additional Resources

- [PHASE8_SUMMARY.md](PHASE8_SUMMARY.md) - Detailed implementation summary
- [PHASE7_SECURITY_NOTES.md](PHASE7_SECURITY_NOTES.md) - Security limitations before Phase 8
- [config.yaml](config.yaml) - Configuration reference
- [API.md](API.md) - API documentation

## Support

For security issues or questions:
1. Check health endpoint: `/health`
2. Review security summary: `/security/summary`
3. Check audit logs for events
4. Consult documentation

**Note**: This is Phase 8. Future phases may add additional security features like JWT sessions, 2FA, and OAuth integration.
