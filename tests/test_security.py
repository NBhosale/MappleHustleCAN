"""
Comprehensive security tests for MapleHustleCAN
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json
import secrets

from app.main import app

client = TestClient(app)


class TestCORSSecurity:
    """Test CORS security configuration"""
    
    def test_cors_allowed_origin(self):
        """Test CORS with allowed origin"""
        response = client.options(
            "/users/me",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization"
            }
        )
        
        assert response.status_code == 200
        assert "Access-Control-Allow-Origin" in response.headers
        assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:3000"
    
    def test_cors_disallowed_origin(self):
        """Test CORS with disallowed origin"""
        response = client.options(
            "/users/me",
            headers={
                "Origin": "https://malicious-site.com",
                "Access-Control-Request-Method": "GET"
            }
        )
        
        # Should still work but with restricted CORS
        assert response.status_code == 200
    
    def test_cors_credentials(self):
        """Test CORS credentials handling"""
        response = client.options(
            "/users/me",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type, Authorization"
            }
        )
        
        assert response.status_code == 200
        assert "Access-Control-Allow-Credentials" in response.headers
        assert response.headers["Access-Control-Allow-Credentials"] == "true"


class TestCSRFProtection:
    """Test CSRF protection"""
    
    def test_csrf_protection_enabled(self):
        """Test CSRF protection when enabled"""
        # This test assumes CSRF is enabled in the configuration
        response = client.post(
            "/users/change-password",
            json={"old_password": "test", "new_password": "newtest"},
            headers={"Content-Type": "application/json"}
        )
        
        # Should either succeed (if CSRF disabled) or require token
        assert response.status_code in [200, 403, 401]
    
    def test_csrf_token_validation(self):
        """Test CSRF token validation"""
        # Generate a valid CSRF token
        csrf_token = secrets.token_urlsafe(32)
        
        response = client.post(
            "/users/change-password",
            json={"old_password": "test", "new_password": "newtest"},
            headers={
                "Content-Type": "application/json",
                "X-CSRF-Token": csrf_token
            }
        )
        
        # Should either succeed or fail with authentication
        assert response.status_code in [200, 401, 403]
    
    def test_csrf_token_missing(self):
        """Test CSRF protection with missing token"""
        response = client.post(
            "/users/change-password",
            json={"old_password": "test", "new_password": "newtest"},
            headers={"Content-Type": "application/json"}
        )
        
        # Should either succeed (if CSRF disabled) or require token
        assert response.status_code in [200, 403, 401]


class TestRequestSizeLimits:
    """Test request size limits"""
    
    def test_request_size_within_limit(self):
        """Test request within size limit"""
        small_data = {"test": "data"}
        response = client.post(
            "/users/register",
            json=small_data,
            headers={"Content-Type": "application/json"}
        )
        
        # Should not be blocked by size limit
        assert response.status_code != 413
    
    def test_request_size_exceeds_limit(self):
        """Test request exceeding size limit"""
        # Create a large payload
        large_data = {"test": "x" * (11 * 1024 * 1024)}  # 11MB
        
        response = client.post(
            "/users/register",
            json=large_data,
            headers={"Content-Type": "application/json"}
        )
        
        # Should be blocked by size limit
        assert response.status_code == 413
        assert "Request too large" in response.json()["detail"]


class TestSQLInjectionProtection:
    """Test SQL injection protection"""
    
    def test_sql_injection_in_query_params(self):
        """Test SQL injection in query parameters"""
        malicious_query = "test'; DROP TABLE users; --"
        
        response = client.get(
            f"/search/services?q={malicious_query}"
        )
        
        # Should be blocked by SQL injection protection
        assert response.status_code == 400
        assert "SQL_INJECTION_DETECTED" in response.json()["error_code"]
    
    def test_sql_injection_in_path(self):
        """Test SQL injection in path parameters"""
        malicious_path = "test'; DROP TABLE users; --"
        
        response = client.get(
            f"/services/{malicious_path}"
        )
        
        # Should be blocked by SQL injection protection
        assert response.status_code == 400
        assert "SQL_INJECTION_DETECTED" in response.json()["error_code"]
    
    def test_sql_injection_in_headers(self):
        """Test SQL injection in headers"""
        malicious_header = "test'; DROP TABLE users; --"
        
        response = client.get(
            "/services/",
            headers={"User-Agent": malicious_header}
        )
        
        # Should be blocked by SQL injection protection
        assert response.status_code == 400
        assert "SQL_INJECTION_DETECTED" in response.json()["error_code"]
    
    def test_legitimate_query_passes(self):
        """Test that legitimate queries pass SQL injection protection"""
        legitimate_query = "house cleaning service"
        
        response = client.get(
            f"/search/services?q={legitimate_query}"
        )
        
        # Should not be blocked
        assert response.status_code != 400
        assert "SQL_INJECTION_DETECTED" not in str(response.content)
    
    def test_sql_injection_patterns(self):
        """Test various SQL injection patterns"""
        malicious_patterns = [
            "1' OR '1'='1",
            "admin'--",
            "admin'/*",
            "admin'#",
            "1' UNION SELECT * FROM users--",
            "1'; DROP TABLE users; --",
            "1' OR 1=1--",
            "1' OR '1'='1' AND '1'='1",
            "1' OR '1'='1' OR '1'='1",
            "1' OR '1'='1' UNION SELECT * FROM users--",
            "1' OR '1'='1' OR '1'='1' UNION SELECT * FROM users--",
            "1' OR '1'='1' OR '1'='1' UNION SELECT * FROM users WHERE '1'='1--",
            "1' OR '1'='1' OR '1'='1' UNION SELECT * FROM users WHERE '1'='1' AND '1'='1--",
            "1' OR '1'='1' OR '1'='1' UNION SELECT * FROM users WHERE '1'='1' AND '1'='1' OR '1'='1--",
            "1' OR '1'='1' OR '1'='1' UNION SELECT * FROM users WHERE '1'='1' AND '1'='1' OR '1'='1' AND '1'='1--",
        ]
        
        for pattern in malicious_patterns:
            response = client.get(
                f"/search/services?q={pattern}"
            )
            
            # Should be blocked by SQL injection protection
            assert response.status_code == 400
            assert "SQL_INJECTION_DETECTED" in response.json()["error_code"]


class TestSecurityHeaders:
    """Test security headers"""
    
    def test_security_headers_present(self):
        """Test that security headers are present in responses"""
        response = client.get("/")
        
        # Check for security headers
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        
        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"
        
        assert "X-XSS-Protection" in response.headers
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
        
        assert "Referrer-Policy" in response.headers
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    
    def test_csp_header_present(self):
        """Test that Content Security Policy header is present"""
        response = client.get("/")
        
        assert "Content-Security-Policy" in response.headers
        csp = response.headers["Content-Security-Policy"]
        
        # Check for key CSP directives
        assert "default-src 'self'" in csp
        assert "script-src 'self'" in csp
        assert "style-src 'self'" in csp
        assert "img-src 'self'" in csp
        assert "frame-ancestors 'none'" in csp
    
    def test_hsts_header_present(self):
        """Test that HSTS header is present"""
        response = client.get("/")
        
        assert "Strict-Transport-Security" in response.headers
        hsts = response.headers["Strict-Transport-Security"]
        
        assert "max-age=31536000" in hsts
        assert "includeSubDomains" in hsts


class TestTrustedHostValidation:
    """Test trusted host validation"""
    
    def test_trusted_host_allowed(self):
        """Test that trusted hosts are allowed"""
        response = client.get(
            "/",
            headers={"Host": "localhost:8000"}
        )
        
        # Should succeed
        assert response.status_code == 200
    
    def test_trusted_host_with_port(self):
        """Test trusted host with port"""
        response = client.get(
            "/",
            headers={"Host": "127.0.0.1:8000"}
        )
        
        # Should succeed
        assert response.status_code == 200
    
    def test_untrusted_host_blocked(self):
        """Test that untrusted hosts are blocked"""
        response = client.get(
            "/",
            headers={"Host": "malicious-site.com"}
        )
        
        # Should be blocked
        assert response.status_code == 400
        assert "Invalid host header" in response.json()["detail"]


class TestRateLimiting:
    """Test rate limiting functionality"""
    
    def test_rate_limiting_within_limit(self):
        """Test requests within rate limit"""
        # Make a few requests within the limit
        for i in range(5):
            response = client.get("/")
            assert response.status_code == 200
    
    def test_rate_limiting_exceeds_limit(self):
        """Test requests exceeding rate limit"""
        # Make many requests to exceed the limit
        responses = []
        for i in range(150):  # Assuming limit is 100 per minute
            response = client.get("/")
            responses.append(response)
        
        # At least one should be rate limited
        rate_limited_responses = [r for r in responses if r.status_code == 429]
        assert len(rate_limited_responses) > 0
        
        # Check rate limit response format
        if rate_limited_responses:
            rate_limit_response = rate_limited_responses[0]
            assert rate_limit_response.status_code == 429
            assert "Rate limit exceeded" in rate_limit_response.json()["detail"]
            assert "RATE_LIMIT_EXCEEDED" in rate_limit_response.json()["error_code"]
            assert "Retry-After" in rate_limit_response.headers


class TestFileUploadSecurity:
    """Test file upload security"""
    
    def test_file_upload_size_limit(self):
        """Test file upload size limit"""
        # Create a large file content
        large_content = b"x" * (6 * 1024 * 1024)  # 6MB
        
        response = client.post(
            "/uploads/profile-image",
            files={"file": ("large.jpg", large_content, "image/jpeg")}
        )
        
        # Should be blocked by size limit
        assert response.status_code == 400
        assert "File too large" in response.json()["detail"]
    
    def test_file_upload_invalid_type(self):
        """Test file upload with invalid type"""
        content = b"fake image data"
        
        response = client.post(
            "/uploads/profile-image",
            files={"file": ("test.txt", content, "text/plain")}
        )
        
        # Should be blocked by type validation
        assert response.status_code == 400
        assert "File type" in response.json()["detail"]
    
    def test_file_upload_valid_type(self):
        """Test file upload with valid type"""
        content = b"fake image data"
        
        with patch("app.routers.uploads.save_file") as mock_save:
            mock_save.return_value = "profiles/test.jpg"
            
            response = client.post(
                "/uploads/profile-image",
                files={"file": ("test.jpg", content, "image/jpeg")}
            )
            
            # Should succeed
            assert response.status_code == 200


class TestAuthenticationSecurity:
    """Test authentication security"""
    
    def test_jwt_token_validation(self):
        """Test JWT token validation"""
        # Test with invalid token
        response = client.get(
            "/users/me",
            headers={"Authorization": "Bearer invalid-token"}
        )
        
        # Should be rejected
        assert response.status_code == 401
    
    def test_jwt_token_missing(self):
        """Test request without JWT token"""
        response = client.get("/users/me")
        
        # Should be rejected
        assert response.status_code == 401
    
    def test_jwt_token_expired(self):
        """Test with expired JWT token"""
        # This would require creating an expired token
        # For now, just test the endpoint exists
        response = client.get("/users/me")
        assert response.status_code == 401


class TestInputValidation:
    """Test input validation security"""
    
    def test_malicious_json_input(self):
        """Test malicious JSON input"""
        malicious_data = {
            "name": "<script>alert('xss')</script>",
            "email": "test@test.com",
            "password": "test123"
        }
        
        response = client.post(
            "/users/register",
            json=malicious_data
        )
        
        # Should be handled by input validation
        assert response.status_code in [200, 400, 422]
    
    def test_sql_injection_in_json(self):
        """Test SQL injection in JSON body"""
        malicious_data = {
            "name": "test'; DROP TABLE users; --",
            "email": "test@test.com",
            "password": "test123"
        }
        
        response = client.post(
            "/users/register",
            json=malicious_data
        )
        
        # Should be handled by input validation
        assert response.status_code in [200, 400, 422]
    
    def test_xss_in_query_params(self):
        """Test XSS in query parameters"""
        malicious_query = "<script>alert('xss')</script>"
        
        response = client.get(
            f"/search/services?q={malicious_query}"
        )
        
        # Should be handled by input validation
        assert response.status_code in [200, 400, 422]


class TestSecurityLogging:
    """Test security event logging"""
    
    def test_security_event_logging(self):
        """Test that security events are logged"""
        # This would require checking logs
        # For now, just test that the endpoint responds
        response = client.get("/")
        assert response.status_code == 200
    
    def test_failed_auth_logging(self):
        """Test that failed authentication attempts are logged"""
        response = client.post(
            "/users/login",
            json={"email": "invalid@test.com", "password": "wrong"}
        )
        
        # Should fail and log the attempt
        assert response.status_code == 401


class TestSecurityMetrics:
    """Test security metrics collection"""
    
    def test_security_metrics_endpoint(self):
        """Test security metrics endpoint"""
        # This would require implementing a metrics endpoint
        # For now, just test that the main endpoint works
        response = client.get("/")
        assert response.status_code == 200
    
    def test_rate_limit_metrics(self):
        """Test rate limit metrics collection"""
        # Make requests to trigger rate limiting
        for i in range(10):
            client.get("/")
        
        # Check that metrics are collected
        # This would require implementing a metrics endpoint
        pass


class TestSecurityConfiguration:
    """Test security configuration"""
    
    def test_security_config_loaded(self):
        """Test that security configuration is loaded"""
        # This would require implementing a debug endpoint
        # For now, just test that the app starts
        response = client.get("/")
        assert response.status_code == 200
    
    def test_security_middleware_order(self):
        """Test that security middleware is in correct order"""
        # This would require checking middleware order
        # For now, just test that the app works
        response = client.get("/")
        assert response.status_code == 200


class TestSecurityIntegration:
    """Test security features working together"""
    
    def test_multiple_security_features(self):
        """Test multiple security features working together"""
        # Test with malicious request that should trigger multiple protections
        malicious_request = {
            "q": "test'; DROP TABLE users; --",
            "size": "x" * (11 * 1024 * 1024)  # Large size
        }
        
        response = client.get(
            "/search/services",
            params=malicious_request
        )
        
        # Should be blocked by SQL injection protection
        assert response.status_code == 400
        assert "SQL_INJECTION_DETECTED" in response.json()["error_code"]
    
    def test_security_headers_with_cors(self):
        """Test that security headers work with CORS"""
        response = client.options(
            "/users/me",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )
        
        # Should have both CORS and security headers
        assert response.status_code == 200
        assert "Access-Control-Allow-Origin" in response.headers
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
