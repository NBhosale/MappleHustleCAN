# 🔒 Security Configuration Guide

## Overview
This document outlines the comprehensive security features implemented in MapleHustleCAN and how to configure them for different environments.

## 🛡️ Security Features Implemented

### 1. CORS Configuration
- **Purpose**: Control cross-origin requests
- **Implementation**: `CORSMiddleware` with configurable origins
- **Configuration**: Set `ALLOWED_ORIGINS` environment variable

### 2. CSRF Protection
- **Purpose**: Prevent Cross-Site Request Forgery attacks
- **Implementation**: `CSRFProtectionMiddleware` with token validation
- **Configuration**: Set `ENABLE_CSRF=true` and provide `CSRF_SECRET_KEY`

### 3. Request Size Limits
- **Purpose**: Prevent large request attacks
- **Implementation**: `RequestSizeLimitMiddleware`
- **Configuration**: Set `MAX_REQUEST_SIZE` (default: 10MB)

### 4. SQL Injection Protection
- **Purpose**: Detect and prevent SQL injection attempts
- **Implementation**: `SQLInjectionProtectionMiddleware` with pattern matching
- **Configuration**: Set `SQL_INJECTION_PROTECTION=true`

### 5. Security Headers
- **Purpose**: Add security headers to all responses
- **Implementation**: `SecurityHeadersMiddleware`
- **Headers**: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, etc.

### 6. Trusted Host Validation
- **Purpose**: Prevent Host header injection
- **Implementation**: `TrustedHostMiddleware`
- **Configuration**: Set `ALLOWED_HOSTS` environment variable

### 7. Advanced Rate Limiting
- **Purpose**: Prevent abuse and DoS attacks
- **Implementation**: `AdvancedRateLimitMiddleware` with IP-based tracking
- **Configuration**: Set `RATE_LIMIT_REQUESTS_PER_MINUTE`

## 🔧 Environment Variables

### Required Security Variables
```bash
# CORS Configuration
ALLOWED_ORIGINS=http://localhost:3000,https://maplehustlecan.com
ALLOWED_HOSTS=localhost,maplehustlecan.com,api.maplehustlecan.com

# Request Size Limits
MAX_REQUEST_SIZE=10485760  # 10MB

# CSRF Protection (optional)
ENABLE_CSRF=false
CSRF_SECRET_KEY=your-csrf-secret-key-here
SESSION_SECRET_KEY=your-session-secret-key-here

# HTTPS Configuration
HTTPS_ONLY=false  # Set to true in production
```

### Optional Security Variables
```bash
# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=100

# Security Headers
SECURITY_HEADERS_ENABLED=true
CSP_ENABLED=true
HSTS_ENABLED=true

# SQL Injection Protection
SQL_INJECTION_PROTECTION=true
SQL_INJECTION_LOG_ATTEMPTS=true

# File Upload Security
MAX_FILE_SIZE=5242880  # 5MB
ALLOWED_FILE_TYPES=image/jpeg,image/png,application/pdf
SCAN_UPLOADS_FOR_VIRUSES=false  # Set to true in production
```

## 🚀 Quick Start

### 1. Development Environment
```bash
# Copy the example configuration
cp .env.security.example .env

# Set basic security variables
export ALLOWED_ORIGINS="http://localhost:3000,http://localhost:8080"
export ALLOWED_HOSTS="localhost,127.0.0.1"
export MAX_REQUEST_SIZE="10485760"
export ENABLE_CSRF="false"
export HTTPS_ONLY="false"
```

### 2. Production Environment
```bash
# Set production security variables
export ALLOWED_ORIGINS="https://maplehustlecan.com,https://www.maplehustlecan.com"
export ALLOWED_HOSTS="maplehustlecan.com,www.maplehustlecan.com,api.maplehustlecan.com"
export MAX_REQUEST_SIZE="10485760"
export ENABLE_CSRF="true"
export CSRF_SECRET_KEY="your-production-csrf-secret-key"
export SESSION_SECRET_KEY="your-production-session-secret-key"
export HTTPS_ONLY="true"
export SQL_INJECTION_PROTECTION="true"
export SCAN_UPLOADS_FOR_VIRUSES="true"
```

## 🔍 Security Testing

### 1. CORS Testing
```bash
# Test CORS with allowed origin
curl -H "Origin: https://maplehustlecan.com" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     http://localhost:8000/api/endpoint

# Test CORS with disallowed origin (should fail)
curl -H "Origin: https://malicious-site.com" \
     -H "Access-Control-Request-Method: POST" \
     -X OPTIONS \
     http://localhost:8000/api/endpoint
```

### 2. CSRF Testing
```bash
# Test CSRF protection (should fail without token)
curl -X POST \
     -H "Content-Type: application/json" \
     -d '{"data": "test"}' \
     http://localhost:8000/api/endpoint

# Test CSRF protection (should succeed with token)
curl -X POST \
     -H "Content-Type: application/json" \
     -H "X-CSRF-Token: valid-token" \
     -d '{"data": "test"}' \
     http://localhost:8000/api/endpoint
```

### 3. SQL Injection Testing
```bash
# Test SQL injection protection (should be blocked)
curl "http://localhost:8000/api/search?q=test'; DROP TABLE users; --"

# Test normal search (should work)
curl "http://localhost:8000/api/search?q=normal-search"
```

### 4. Rate Limiting Testing
```bash
# Test rate limiting (should be blocked after limit)
for i in {1..101}; do
  curl "http://localhost:8000/api/endpoint"
done
```

## 📊 Security Monitoring

### 1. Log Analysis
```bash
# Monitor security events
tail -f logs/security.log | grep -E "(SQL_INJECTION|CSRF|RATE_LIMIT)"

# Monitor failed authentication attempts
tail -f logs/auth.log | grep "FAILED_AUTH"

# Monitor file uploads
tail -f logs/uploads.log | grep -E "(UPLOAD|VIRUS_SCAN)"
```

### 2. Metrics Collection
```bash
# Security metrics endpoint
curl http://localhost:8000/metrics/security

# Rate limiting metrics
curl http://localhost:8000/metrics/rate-limit

# SQL injection attempt metrics
curl http://localhost:8000/metrics/sql-injection
```

## 🚨 Security Alerts

### 1. Email Alerts
Configure email alerts for security events:
```python
# In your environment
export SECURITY_ALERTS_ENABLED=true
export ALERT_EMAIL=security@maplehustlecan.com
```

### 2. Webhook Alerts
Configure webhook alerts for real-time notifications:
```python
# In your environment
export ALERT_WEBHOOK_URL=https://hooks.slack.com/services/your/webhook/url
```

## 🔧 Customization

### 1. Custom CORS Configuration
```python
# In app/core/security.py
def configure_cors(app: FastAPI, allowed_origins: List[str] = None):
    if allowed_origins is None:
        allowed_origins = [
            "http://localhost:3000",
            "https://maplehustlecan.com",
            # Add your custom origins
        ]
    # ... rest of configuration
```

### 2. Custom Rate Limiting
```python
# In app/core/security.py
class AdvancedRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.max_requests = 100  # Customize limit
        self.window_minutes = 1  # Customize window
```

### 3. Custom SQL Injection Patterns
```python
# In app/core/security.py
class SQLInjectionProtectionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.sql_patterns = [
            # Add your custom patterns
            r"(\bCUSTOM_PATTERN\b)",
        ]
```

## 📚 Best Practices

### 1. Development
- Use `ENABLE_CSRF=false` for API-only development
- Set `HTTPS_ONLY=false` for local development
- Use `DEBUG=true` for detailed error messages
- Set `LOG_LEVEL=DEBUG` for verbose logging

### 2. Staging
- Use `ENABLE_CSRF=true` to test CSRF protection
- Set `HTTPS_ONLY=true` to test HTTPS requirements
- Use `DEBUG=false` for production-like behavior
- Set `LOG_LEVEL=INFO` for normal logging

### 3. Production
- Use `ENABLE_CSRF=true` for full protection
- Set `HTTPS_ONLY=true` for security
- Use `DEBUG=false` for security
- Set `LOG_LEVEL=WARNING` for minimal logging
- Enable `SCAN_UPLOADS_FOR_VIRUSES=true`
- Use strong secret keys
- Monitor security logs regularly

## 🆘 Troubleshooting

### Common Issues

1. **CORS Errors**
   - Check `ALLOWED_ORIGINS` configuration
   - Verify origin is in the allowed list
   - Check for typos in domain names

2. **CSRF Token Errors**
   - Verify `ENABLE_CSRF` is set correctly
   - Check `CSRF_SECRET_KEY` is provided
   - Ensure token is sent in `X-CSRF-Token` header

3. **Rate Limiting Issues**
   - Check `RATE_LIMIT_REQUESTS_PER_MINUTE` setting
   - Verify rate limiting is enabled
   - Check for IP address issues

4. **SQL Injection False Positives**
   - Review SQL injection patterns
   - Add legitimate patterns to whitelist
   - Check for special characters in legitimate data

### Debug Commands

```bash
# Check security configuration
curl http://localhost:8000/debug/security-config

# Check rate limiting status
curl http://localhost:8000/debug/rate-limit-status

# Check SQL injection protection status
curl http://localhost:8000/debug/sql-injection-status
```

## 📖 Additional Resources

- [OWASP Security Guidelines](https://owasp.org/www-project-top-ten/)
- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [CORS Security Guide](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [CSRF Protection Guide](https://owasp.org/www-community/attacks/csrf)
- [SQL Injection Prevention](https://owasp.org/www-community/attacks/SQL_Injection)
