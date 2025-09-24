"""
Advanced security hardening measures for MapleHustleCAN
"""
import hashlib
import hmac
import ipaddress
import logging
import re
import secrets
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

import bcrypt
from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security_monitoring import SecurityEvent, SecurityEventType, SecurityMonitor
from app.models.users import User

logger = logging.getLogger(__name__)


class SecurityHardening:
    """Advanced security hardening utilities"""

    def __init__(self):
        self.security_monitor = SecurityMonitor({
            "enabled": settings.SECURITY_MONITORING_ENABLED,
            "anomaly_detection": True,
            "alerting": True
        })
        
        # Security patterns
        self.malicious_patterns = [
            r"<script[^>]*>.*?</script>",  # XSS
            r"javascript:",  # JavaScript injection
            r"vbscript:",  # VBScript injection
            r"onload\s*=",  # Event handler injection
            r"onerror\s*=",  # Event handler injection
            r"onclick\s*=",  # Event handler injection
            r"union\s+select",  # SQL injection
            r"drop\s+table",  # SQL injection
            r"delete\s+from",  # SQL injection
            r"insert\s+into",  # SQL injection
            r"update\s+set",  # SQL injection
            r"exec\s*\(",  # Command injection
            r"system\s*\(",  # Command injection
            r"eval\s*\(",  # Code injection
            r"base64_decode",  # Obfuscation
            r"chr\s*\(",  # Character encoding
            r"char\s*\(",  # Character encoding
            r"concat\s*\(",  # String concatenation
            r"substring\s*\(",  # String manipulation
            r"ascii\s*\(",  # ASCII conversion
            r"hex\s*\(",  # Hexadecimal conversion
            r"unhex\s*\(",  # Hexadecimal decoding
            r"load_file\s*\(",  # File access
            r"into\s+outfile",  # File writing
            r"into\s+dumpfile",  # File writing
            r"benchmark\s*\(",  # Time-based attacks
            r"sleep\s*\(",  # Time-based attacks
            r"waitfor\s+delay",  # Time-based attacks
            r"pg_sleep\s*\(",  # PostgreSQL sleep
            r"dbms_pipe",  # Oracle pipe
            r"xp_cmdshell",  # SQL Server command shell
            r"sp_executesql",  # SQL Server dynamic SQL
            r"@@version",  # Version information
            r"@@hostname",  # Hostname information
            r"@@datadir",  # Data directory
            r"information_schema",  # Information schema
            r"sys\.",  # System tables
            r"mysql\.",  # MySQL system tables
            r"pg_",  # PostgreSQL system tables
            r"sysobjects",  # SQL Server system tables
            r"syscolumns",  # SQL Server system tables
            r"sysusers",  # SQL Server system tables
            r"sysdatabases",  # SQL Server system tables
            r"sysprocesses",  # SQL Server system tables
            r"sysfiles",  # SQL Server system tables
            r"sysfilegroups",  # SQL Server system tables
            r"sysindexes",  # SQL Server system tables
            r"sysindexkeys",  # SQL Server system tables
            r"sysforeignkeys",  # SQL Server system tables
            r"sysreferences",  # SQL Server system tables
            r"sysconstraints",  # SQL Server system tables
            r"syscomments",  # SQL Server system tables
            r"sysdepends",  # SQL Server system tables
            r"syspermissions",  # SQL Server system tables
            r"sysprotects",  # SQL Server system tables
            r"sysmembers",  # SQL Server system tables
            r"syslogins",  # SQL Server system tables
            r"sysremotelogins",  # SQL Server system tables
            r"sysservers",  # SQL Server system tables
            r"sysdatabases",  # SQL Server system tables
            r"sysdevices",  # SQL Server system tables
            r"sysusages",  # SQL Server system tables
            r"syslocks",  # SQL Server system tables
            r"sysprocesses",  # SQL Server system tables
            r"syscacheobjects",  # SQL Server system tables
            r"syslockinfo",  # SQL Server system tables
            r"syslockstats",  # SQL Server system tables
            r"syslockinfo",  # SQL Server system tables
            r"syslockstats",  # SQL Server system tables
            r"syslockinfo",  # SQL Server system tables
            r"syslockstats",  # SQL Server system tables
        ]
        
        # Compile patterns for better performance
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.malicious_patterns]
        
        # IP reputation tracking
        self.suspicious_ips: Set[str] = set()
        self.blocked_ips: Set[str] = set()
        self.ip_attempts: Dict[str, List[datetime]] = {}
        
        # Account lockout tracking
        self.failed_attempts: Dict[str, List[datetime]] = {}
        self.locked_accounts: Set[str] = set()
        
        # Rate limiting per IP
        self.ip_requests: Dict[str, List[datetime]] = {}
        
        # Security headers
        self.security_headers = {
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), gyroscope=(), accelerometer=()",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https: blob:; "
                "font-src 'self' data: https:; "
                "connect-src 'self' https: wss:; "
                "media-src 'self' data: https:; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "form-action 'self'; "
                "frame-ancestors 'none'; "
                "upgrade-insecure-requests; "
                "block-all-mixed-content"
            ),
            "X-Permitted-Cross-Domain-Policies": "none",
            "Cross-Origin-Embedder-Policy": "require-corp",
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Resource-Policy": "same-origin",
            "X-DNS-Prefetch-Control": "off",
            "X-Download-Options": "noopen",
            "X-Powered-By": "",  # Remove server identification
        }

    def detect_malicious_input(self, input_data: str) -> bool:
        """Detect malicious input patterns"""
        if not input_data:
            return False
        
        # Check against compiled patterns
        for pattern in self.compiled_patterns:
            if pattern.search(input_data):
                return True
        
        # Additional checks
        if self._contains_suspicious_characters(input_data):
            return True
        
        if self._contains_encoded_payloads(input_data):
            return True
        
        return False

    def _contains_suspicious_characters(self, input_data: str) -> bool:
        """Check for suspicious character sequences"""
        suspicious_chars = [
            "..",  # Directory traversal
            "\\x",  # Hexadecimal encoding
            "%00",  # Null byte
            "%0a",  # Line feed
            "%0d",  # Carriage return
            "%09",  # Tab
            "%20",  # Space
            "%22",  # Quote
            "%27",  # Apostrophe
            "%3c",  # Less than
            "%3e",  # Greater than
            "%26",  # Ampersand
            "%2f",  # Forward slash
            "%5c",  # Backslash
            "%3f",  # Question mark
            "%3d",  # Equals
            "%2b",  # Plus
            "%23",  # Hash
            "%24",  # Dollar
            "%25",  # Percent
            "%2a",  # Asterisk
            "%28",  # Left parenthesis
            "%29",  # Right parenthesis
            "%5b",  # Left bracket
            "%5d",  # Right bracket
            "%7b",  # Left brace
            "%7d",  # Right brace
            "%7c",  # Pipe
            "%5e",  # Caret
            "%60",  # Backtick
            "%7e",  # Tilde
        ]
        
        input_lower = input_data.lower()
        return any(char in input_lower for char in suspicious_chars)

    def _contains_encoded_payloads(self, input_data: str) -> bool:
        """Check for encoded payloads"""
        # Check for base64-like patterns
        if re.search(r'[A-Za-z0-9+/]{20,}={0,2}', input_data):
            return True
        
        # Check for URL encoding
        if re.search(r'%[0-9A-Fa-f]{2}', input_data):
            return True
        
        # Check for HTML entities
        if re.search(r'&[a-zA-Z]+;', input_data):
            return True
        
        return False

    def validate_password_strength(self, password: str) -> Tuple[bool, List[str]]:
        """Validate password strength"""
        errors = []
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        
        if len(password) > 128:
            errors.append("Password must be less than 128 characters")
        
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not re.search(r'[0-9]', password):
            errors.append("Password must contain at least one digit")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        # Check for common patterns
        if re.search(r'(.)\1{2,}', password):
            errors.append("Password must not contain repeated characters")
        
        if re.search(r'(012|123|234|345|456|567|678|789|890)', password):
            errors.append("Password must not contain sequential numbers")
        
        if re.search(r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)', password.lower()):
            errors.append("Password must not contain sequential letters")
        
        # Check for common passwords
        common_passwords = [
            "password", "123456", "123456789", "qwerty", "abc123",
            "password123", "admin", "letmein", "welcome", "monkey",
            "1234567890", "password1", "qwerty123", "dragon", "master",
            "hello", "freedom", "whatever", "qazwsx", "trustno1"
        ]
        
        if password.lower() in common_passwords:
            errors.append("Password is too common")
        
        return len(errors) == 0, errors

    def validate_email_security(self, email: str) -> Tuple[bool, List[str]]:
        """Validate email security"""
        errors = []
        
        if not email or len(email) > 254:
            errors.append("Invalid email length")
            return False, errors
        
        # Check for valid email format
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            errors.append("Invalid email format")
            return False, errors
        
        # Check for suspicious patterns
        if self.detect_malicious_input(email):
            errors.append("Email contains suspicious content")
            return False, errors
        
        # Check for disposable email domains
        disposable_domains = [
            "10minutemail.com", "tempmail.org", "guerrillamail.com",
            "mailinator.com", "throwaway.email", "temp-mail.org"
        ]
        
        domain = email.split('@')[1].lower()
        if domain in disposable_domains:
            errors.append("Disposable email addresses are not allowed")
            return False, errors
        
        return True, errors

    def check_ip_reputation(self, ip: str) -> Tuple[bool, str]:
        """Check IP reputation and block suspicious IPs"""
        try:
            # Validate IP address
            ipaddress.ip_address(ip)
        except ValueError:
            return False, "Invalid IP address"
        
        # Check if IP is blocked
        if ip in self.blocked_ips:
            return False, "IP is blocked"
        
        # Check if IP is suspicious
        if ip in self.suspicious_ips:
            return False, "IP is flagged as suspicious"
        
        # Check for too many requests from this IP
        now = datetime.now()
        if ip in self.ip_requests:
            # Remove old requests (older than 1 hour)
            self.ip_requests[ip] = [
                req_time for req_time in self.ip_requests[ip]
                if now - req_time < timedelta(hours=1)
            ]
            
            # Check rate limit (100 requests per hour)
            if len(self.ip_requests[ip]) > 100:
                self.blocked_ips.add(ip)
                return False, "IP rate limit exceeded"
        
        # Record this request
        if ip not in self.ip_requests:
            self.ip_requests[ip] = []
        self.ip_requests[ip].append(now)
        
        return True, "IP is clean"

    def check_account_lockout(self, email: str) -> Tuple[bool, str]:
        """Check if account is locked out due to failed attempts"""
        if email in self.locked_accounts:
            return False, "Account is locked due to too many failed attempts"
        
        now = datetime.now()
        if email in self.failed_attempts:
            # Remove old attempts (older than 1 hour)
            self.failed_attempts[email] = [
                attempt_time for attempt_time in self.failed_attempts[email]
                if now - attempt_time < timedelta(hours=1)
            ]
            
            # Check if too many failed attempts (5 per hour)
            if len(self.failed_attempts[email]) >= 5:
                self.locked_accounts.add(email)
                return False, "Account locked due to too many failed attempts"
        
        return True, "Account is not locked"

    def record_failed_attempt(self, email: str, ip: str):
        """Record a failed authentication attempt"""
        now = datetime.now()
        
        # Record failed attempt for email
        if email not in self.failed_attempts:
            self.failed_attempts[email] = []
        self.failed_attempts[email].append(now)
        
        # Record failed attempt for IP
        if ip not in self.ip_attempts:
            self.ip_attempts[ip] = []
        self.ip_attempts[ip].append(now)
        
        # Check if IP should be flagged as suspicious
        if len(self.ip_attempts[ip]) >= 10:  # 10 failed attempts from same IP
            self.suspicious_ips.add(ip)
        
        # Record security event
        event = SecurityEvent(
            event_type=SecurityEventType.FAILED_AUTHENTICATION,
            client_ip=ip,
            user_agent="",
            request_path="/auth/login",
            details={"email": email, "attempt_count": len(self.failed_attempts[email])}
        )
        self.security_monitor.record_event(event)

    def generate_secure_token(self, length: int = 32) -> str:
        """Generate a cryptographically secure token"""
        return secrets.token_urlsafe(length)

    def hash_password(self, password: str) -> str:
        """Hash password with bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

    def generate_csrf_token(self, session_id: str) -> str:
        """Generate CSRF token"""
        secret = settings.JWT_SECRET_KEY
        data = f"{session_id}:{int(time.time())}"
        return hmac.new(
            secret.encode('utf-8'),
            data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    def verify_csrf_token(self, token: str, session_id: str) -> bool:
        """Verify CSRF token"""
        secret = settings.JWT_SECRET_KEY
        data = f"{session_id}:{int(time.time())}"
        expected_token = hmac.new(
            secret.encode('utf-8'),
            data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(token, expected_token)

    def sanitize_input(self, input_data: str) -> str:
        """Sanitize input data"""
        if not input_data:
            return ""
        
        # Remove null bytes
        input_data = input_data.replace('\x00', '')
        
        # Remove control characters
        input_data = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', input_data)
        
        # Normalize whitespace
        input_data = re.sub(r'\s+', ' ', input_data).strip()
        
        # Limit length
        if len(input_data) > 10000:  # 10KB limit
            input_data = input_data[:10000]
        
        return input_data

    def validate_file_upload(self, filename: str, content_type: str, file_size: int) -> Tuple[bool, str]:
        """Validate file upload security"""
        # Check file extension
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx', '.txt'}
        file_ext = '.' + filename.split('.')[-1].lower() if '.' in filename else ''
        
        if file_ext not in allowed_extensions:
            return False, "File type not allowed"
        
        # Check content type
        allowed_content_types = {
            'image/jpeg', 'image/png', 'image/gif', 'application/pdf',
            'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain'
        }
        
        if content_type not in allowed_content_types:
            return False, "Content type not allowed"
        
        # Check file size (5MB limit)
        max_size = 5 * 1024 * 1024
        if file_size > max_size:
            return False, "File too large"
        
        # Check filename for malicious patterns
        if self.detect_malicious_input(filename):
            return False, "Filename contains suspicious content"
        
        return True, "File upload is valid"

    def get_security_headers(self) -> Dict[str, str]:
        """Get security headers"""
        return self.security_headers.copy()

    def get_security_metrics(self) -> Dict[str, Any]:
        """Get security metrics"""
        return {
            "blocked_ips": len(self.blocked_ips),
            "suspicious_ips": len(self.suspicious_ips),
            "locked_accounts": len(self.locked_accounts),
            "total_failed_attempts": sum(len(attempts) for attempts in self.failed_attempts.values()),
            "security_events": self.security_monitor.get_metrics()
        }

    def cleanup_expired_data(self):
        """Clean up expired security data"""
        now = datetime.now()
        
        # Clean up old IP requests
        for ip in list(self.ip_requests.keys()):
            self.ip_requests[ip] = [
                req_time for req_time in self.ip_requests[ip]
                if now - req_time < timedelta(hours=1)
            ]
            if not self.ip_requests[ip]:
                del self.ip_requests[ip]
        
        # Clean up old failed attempts
        for email in list(self.failed_attempts.keys()):
            self.failed_attempts[email] = [
                attempt_time for attempt_time in self.failed_attempts[email]
                if now - attempt_time < timedelta(hours=1)
            ]
            if not self.failed_attempts[email]:
                del self.failed_attempts[email]
        
        # Clean up old IP attempts
        for ip in list(self.ip_attempts.keys()):
            self.ip_attempts[ip] = [
                attempt_time for attempt_time in self.ip_attempts[ip]
                if now - attempt_time < timedelta(hours=1)
            ]
            if not self.ip_attempts[ip]:
                del self.ip_attempts[ip]


# Global security hardening instance
_security_hardening: Optional[SecurityHardening] = None


def get_security_hardening() -> SecurityHardening:
    """Get global security hardening instance"""
    global _security_hardening
    if _security_hardening is None:
        _security_hardening = SecurityHardening()
    return _security_hardening


# Security middleware
class SecurityHardeningMiddleware:
    """Middleware for security hardening"""
    
    def __init__(self, app):
        self.app = app
        self.security = get_security_hardening()
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Check IP reputation
        is_clean, message = self.security.check_ip_reputation(client_ip)
        if not is_clean:
            # Block the request
            response = HTTPException(
                status_code=403,
                detail=f"Access denied: {message}"
            )
            await response(scope, receive, send)
            return
        
        # Check for malicious input in query parameters
        for param, value in request.query_params.items():
            if self.security.detect_malicious_input(str(value)):
                event = SecurityEvent(
                    event_type=SecurityEventType.MALICIOUS_REQUEST,
                    client_ip=client_ip,
                    user_agent=request.headers.get("user-agent", ""),
                    request_path=request.url.path,
                    details={"parameter": param, "value": str(value)[:100]}
                )
                self.security.security_monitor.record_event(event)
                
                response = HTTPException(
                    status_code=400,
                    detail="Malicious input detected"
                )
                await response(scope, receive, send)
                return
        
        # Process request
        await self.app(scope, receive, send)
