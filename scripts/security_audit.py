#!/usr/bin/env python3
"""
Comprehensive security audit script for MapleHustleCAN
"""
import asyncio
import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.db.session import get_engine
from app.core.security_hardening import get_security_hardening
from app.core.config import settings


class SecurityAuditor:
    """Comprehensive security auditor"""

    def __init__(self):
        self.engine = get_engine()
        self.security = get_security_hardening()
        self.audit_results = {
            "timestamp": "2024-01-01T00:00:00Z",
            "overall_score": 0,
            "categories": {},
            "recommendations": [],
            "critical_issues": [],
            "warnings": [],
            "info": []
        }

    async def run_full_audit(self):
        """Run comprehensive security audit"""
        print("🔒 Starting MapleHustleCAN Security Audit")
        print("=" * 60)
        
        # 1. Authentication & Authorization Audit
        await self.audit_authentication()
        
        # 2. Database Security Audit
        await self.audit_database_security()
        
        # 3. API Security Audit
        await self.audit_api_security()
        
        # 4. Input Validation Audit
        await self.audit_input_validation()
        
        # 5. File Upload Security Audit
        await self.audit_file_upload_security()
        
        # 6. Session Management Audit
        await self.audit_session_management()
        
        # 7. Encryption & Hashing Audit
        await self.audit_encryption()
        
        # 8. Network Security Audit
        await self.audit_network_security()
        
        # 9. Logging & Monitoring Audit
        await self.audit_logging_monitoring()
        
        # 10. Configuration Security Audit
        await self.audit_configuration()
        
        # Calculate overall score
        self.calculate_overall_score()
        
        # Generate report
        self.generate_report()
        
        return self.audit_results

    async def audit_authentication(self):
        """Audit authentication and authorization"""
        print("🔐 Auditing Authentication & Authorization...")
        
        issues = []
        score = 100
        
        with self.engine.connect() as conn:
            # Check password policies
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total_users,
                    COUNT(CASE WHEN LENGTH(hashed_password) < 60 THEN 1 END) as weak_passwords
                FROM users
            """))
            
            stats = result.fetchone()
            if stats.weak_passwords > 0:
                issues.append(f"Found {stats.weak_passwords} users with weak password hashes")
                score -= 20
            
            # Check for default passwords
            result = conn.execute(text("""
                SELECT COUNT(*) as default_passwords
                FROM users
                WHERE hashed_password = 'admin' OR hashed_password = 'password'
            """))
            
            default_count = result.scalar()
            if default_count > 0:
                issues.append(f"Found {default_count} users with default passwords")
                score -= 30
            
            # Check for admin accounts
            result = conn.execute(text("""
                SELECT COUNT(*) as admin_count
                FROM users
                WHERE role = 'admin'
            """))
            
            admin_count = result.scalar()
            if admin_count == 0:
                issues.append("No admin accounts found")
                score -= 10
            elif admin_count > 5:
                issues.append(f"Too many admin accounts: {admin_count}")
                score -= 5
            
            # Check for inactive accounts
            result = conn.execute(text("""
                SELECT COUNT(*) as inactive_count
                FROM users
                WHERE status = 'inactive'
            """))
            
            inactive_count = result.scalar()
            if inactive_count > 0:
                issues.append(f"Found {inactive_count} inactive accounts")
                score -= 5
        
        self.audit_results["categories"]["authentication"] = {
            "score": max(0, score),
            "issues": issues,
            "status": "pass" if score >= 80 else "fail"
        }
        
        if score < 80:
            self.audit_results["critical_issues"].extend(issues)

    async def audit_database_security(self):
        """Audit database security"""
        print("🗄️  Auditing Database Security...")
        
        issues = []
        score = 100
        
        with self.engine.connect() as conn:
            # Check for RLS policies
            result = conn.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    rowsecurity
                FROM pg_tables 
                WHERE schemaname = 'public'
                AND rowsecurity = false
            """))
            
            unprotected_tables = list(result)
            if unprotected_tables:
                issues.append(f"Found {len(unprotected_tables)} tables without RLS")
                score -= 15
            
            # Check for sensitive data exposure
            result = conn.execute(text("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND (column_name ILIKE '%password%' 
                     OR column_name ILIKE '%secret%'
                     OR column_name ILIKE '%key%'
                     OR column_name ILIKE '%token%')
            """))
            
            sensitive_columns = list(result)
            if sensitive_columns:
                issues.append(f"Found {len(sensitive_columns)} potentially sensitive columns")
                score -= 10
            
            # Check for proper indexing
            result = conn.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname
                FROM pg_indexes
                WHERE schemaname = 'public'
                AND indexname LIKE '%security%'
            """))
            
            security_indexes = list(result)
            if not security_indexes:
                issues.append("No security-related indexes found")
                score -= 5
            
            # Check for database permissions
            result = conn.execute(text("""
                SELECT 
                    grantee,
                    privilege_type
                FROM information_schema.role_table_grants
                WHERE table_schema = 'public'
                AND privilege_type = 'DELETE'
            """))
            
            delete_permissions = list(result)
            if len(delete_permissions) > 1:  # More than just the owner
                issues.append("Multiple users have DELETE permissions")
                score -= 10
        
        self.audit_results["categories"]["database"] = {
            "score": max(0, score),
            "issues": issues,
            "status": "pass" if score >= 80 else "fail"
        }
        
        if score < 80:
            self.audit_results["warnings"].extend(issues)

    async def audit_api_security(self):
        """Audit API security"""
        print("🌐 Auditing API Security...")
        
        issues = []
        score = 100
        
        # Check for HTTPS enforcement
        if not settings.ENVIRONMENT == "production":
            issues.append("Not running in production mode")
            score -= 5
        
        # Check for CORS configuration
        if not settings.ALLOWED_ORIGINS:
            issues.append("CORS not properly configured")
            score -= 10
        
        # Check for rate limiting
        if not settings.REDIS_URL:
            issues.append("Rate limiting not enabled (no Redis)")
            score -= 15
        
        # Check for JWT configuration
        if not settings.JWT_SECRET_KEY or len(settings.JWT_SECRET_KEY) < 32:
            issues.append("JWT secret key is weak or not configured")
            score -= 20
        
        # Check for security headers
        required_headers = [
            "X-Frame-Options",
            "X-Content-Type-Options",
            "X-XSS-Protection",
            "Strict-Transport-Security"
        ]
        
        # This would be checked in actual HTTP responses
        issues.append("Security headers should be verified in HTTP responses")
        score -= 5
        
        self.audit_results["categories"]["api"] = {
            "score": max(0, score),
            "issues": issues,
            "status": "pass" if score >= 80 else "fail"
        }
        
        if score < 80:
            self.audit_results["warnings"].extend(issues)

    async def audit_input_validation(self):
        """Audit input validation"""
        print("📝 Auditing Input Validation...")
        
        issues = []
        score = 100
        
        # Test malicious inputs
        test_inputs = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
            "../../etc/passwd",
            "javascript:alert('xss')",
            "{{7*7}}",
            "${7*7}",
            "#{7*7}",
            "<%=7*7%>",
            "{{config}}",
            "${config}",
            "#{config}",
            "<%=config%>"
        ]
        
        for test_input in test_inputs:
            if not self.security.detect_malicious_input(test_input):
                issues.append(f"Failed to detect malicious input: {test_input[:50]}...")
                score -= 10
        
        # Check password validation
        weak_passwords = [
            "password",
            "123456",
            "admin",
            "qwerty",
            "abc123"
        ]
        
        for weak_password in weak_passwords:
            is_valid, errors = self.security.validate_password_strength(weak_password)
            if is_valid:
                issues.append(f"Failed to reject weak password: {weak_password}")
                score -= 5
        
        # Check email validation
        invalid_emails = [
            "invalid-email",
            "test@",
            "@example.com",
            "test@.com",
            "test@example",
            "test@example..com"
        ]
        
        for invalid_email in invalid_emails:
            is_valid, errors = self.security.validate_email_security(invalid_email)
            if is_valid:
                issues.append(f"Failed to reject invalid email: {invalid_email}")
                score -= 5
        
        self.audit_results["categories"]["input_validation"] = {
            "score": max(0, score),
            "issues": issues,
            "status": "pass" if score >= 80 else "fail"
        }
        
        if score < 80:
            self.audit_results["critical_issues"].extend(issues)

    async def audit_file_upload_security(self):
        """Audit file upload security"""
        print("📁 Auditing File Upload Security...")
        
        issues = []
        score = 100
        
        # Test file validation
        test_files = [
            ("malicious.exe", "application/x-executable", 1024),
            ("script.php", "application/x-php", 1024),
            ("test.jpg", "image/jpeg", 6 * 1024 * 1024),  # Too large
            ("test.txt", "text/plain", 1024),
            ("test.jpg", "image/jpeg", 1024),  # Valid
        ]
        
        for filename, content_type, file_size in test_files:
            is_valid, message = self.security.validate_file_upload(filename, content_type, file_size)
            if filename == "test.jpg" and content_type == "image/jpeg" and file_size == 1024:
                # This should be valid
                if not is_valid:
                    issues.append(f"Failed to accept valid file: {filename}")
                    score -= 10
            else:
                # These should be invalid
                if is_valid:
                    issues.append(f"Failed to reject invalid file: {filename}")
                    score -= 15
        
        self.audit_results["categories"]["file_upload"] = {
            "score": max(0, score),
            "issues": issues,
            "status": "pass" if score >= 80 else "fail"
        }
        
        if score < 80:
            self.audit_results["warnings"].extend(issues)

    async def audit_session_management(self):
        """Audit session management"""
        print("🔑 Auditing Session Management...")
        
        issues = []
        score = 100
        
        # Check JWT configuration
        if not settings.JWT_SECRET_KEY:
            issues.append("JWT secret key not configured")
            score -= 30
        
        if len(settings.JWT_SECRET_KEY) < 32:
            issues.append("JWT secret key too short")
            score -= 20
        
        # Check refresh token configuration
        if not hasattr(settings, 'REFRESH_TOKEN_EXPIRE_DAYS'):
            issues.append("Refresh token expiration not configured")
            score -= 10
        
        # Check session timeout
        if not hasattr(settings, 'SESSION_TIMEOUT'):
            issues.append("Session timeout not configured")
            score -= 5
        
        self.audit_results["categories"]["session_management"] = {
            "score": max(0, score),
            "issues": issues,
            "status": "pass" if score >= 80 else "fail"
        }
        
        if score < 80:
            self.audit_results["warnings"].extend(issues)

    async def audit_encryption(self):
        """Audit encryption and hashing"""
        print("🔐 Auditing Encryption & Hashing...")
        
        issues = []
        score = 100
        
        # Check password hashing
        test_password = "test_password_123"
        hashed = self.security.hash_password(test_password)
        
        if not self.security.verify_password(test_password, hashed):
            issues.append("Password hashing/verification failed")
            score -= 30
        
        # Check if bcrypt is being used
        if not hashed.startswith('$2b$'):
            issues.append("Not using bcrypt for password hashing")
            score -= 20
        
        # Check for weak hashing
        if len(hashed) < 60:
            issues.append("Password hash too short")
            score -= 15
        
        # Check token generation
        token = self.security.generate_secure_token()
        if len(token) < 32:
            issues.append("Generated token too short")
            score -= 10
        
        self.audit_results["categories"]["encryption"] = {
            "score": max(0, score),
            "issues": issues,
            "status": "pass" if score >= 80 else "fail"
        }
        
        if score < 80:
            self.audit_results["critical_issues"].extend(issues)

    async def audit_network_security(self):
        """Audit network security"""
        print("🌐 Auditing Network Security...")
        
        issues = []
        score = 100
        
        # Check for HTTPS enforcement
        if settings.ENVIRONMENT == "production" and not settings.HTTPS_ONLY:
            issues.append("HTTPS not enforced in production")
            score -= 20
        
        # Check for CORS configuration
        if not settings.ALLOWED_ORIGINS:
            issues.append("CORS not configured")
            score -= 10
        
        # Check for trusted hosts
        if not settings.ALLOWED_HOSTS:
            issues.append("Trusted hosts not configured")
            score -= 10
        
        # Check for rate limiting
        if not settings.REDIS_URL:
            issues.append("Rate limiting not enabled")
            score -= 15
        
        self.audit_results["categories"]["network"] = {
            "score": max(0, score),
            "issues": issues,
            "status": "pass" if score >= 80 else "fail"
        }
        
        if score < 80:
            self.audit_results["warnings"].extend(issues)

    async def audit_logging_monitoring(self):
        """Audit logging and monitoring"""
        print("📊 Auditing Logging & Monitoring...")
        
        issues = []
        score = 100
        
        # Check for security monitoring
        if not settings.SECURITY_MONITORING_ENABLED:
            issues.append("Security monitoring not enabled")
            score -= 20
        
        # Check for error tracking
        if not settings.SENTRY_DSN:
            issues.append("Error tracking not configured")
            score -= 10
        
        # Check for logging level
        if settings.LOG_LEVEL.upper() not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            issues.append("Invalid log level configured")
            score -= 5
        
        self.audit_results["categories"]["logging_monitoring"] = {
            "score": max(0, score),
            "issues": issues,
            "status": "pass" if score >= 80 else "fail"
        }
        
        if score < 80:
            self.audit_results["warnings"].extend(issues)

    async def audit_configuration(self):
        """Audit configuration security"""
        print("⚙️  Auditing Configuration Security...")
        
        issues = []
        score = 100
        
        # Check for debug mode in production
        if settings.ENVIRONMENT == "production" and settings.DEBUG:
            issues.append("Debug mode enabled in production")
            score -= 30
        
        # Check for weak secrets
        if settings.JWT_SECRET_KEY == "your-secret-key-here":
            issues.append("Default JWT secret key in use")
            score -= 25
        
        # Check for missing environment variables
        required_vars = [
            "DATABASE_URL",
            "JWT_SECRET_KEY",
            "ENVIRONMENT"
        ]
        
        for var in required_vars:
            if not getattr(settings, var, None):
                issues.append(f"Required environment variable {var} not set")
                score -= 15
        
        # Check for insecure defaults
        if settings.ALLOWED_ORIGINS == ["*"]:
            issues.append("CORS allows all origins")
            score -= 20
        
        self.audit_results["categories"]["configuration"] = {
            "score": max(0, score),
            "issues": issues,
            "status": "pass" if score >= 80 else "fail"
        }
        
        if score < 80:
            self.audit_results["critical_issues"].extend(issues)

    def calculate_overall_score(self):
        """Calculate overall security score"""
        categories = self.audit_results["categories"]
        if not categories:
            self.audit_results["overall_score"] = 0
            return
        
        total_score = sum(cat["score"] for cat in categories.values())
        self.audit_results["overall_score"] = total_score / len(categories)

    def generate_report(self):
        """Generate security audit report"""
        print("\n" + "=" * 60)
        print("🔒 SECURITY AUDIT REPORT")
        print("=" * 60)
        
        overall_score = self.audit_results["overall_score"]
        print(f"Overall Security Score: {overall_score:.1f}/100")
        
        if overall_score >= 90:
            print("🟢 EXCELLENT - Security is well implemented")
        elif overall_score >= 80:
            print("🟡 GOOD - Minor security improvements needed")
        elif overall_score >= 70:
            print("🟠 FAIR - Several security issues need attention")
        else:
            print("🔴 POOR - Critical security issues require immediate attention")
        
        print("\n📊 Category Scores:")
        for category, data in self.audit_results["categories"].items():
            status_icon = "🟢" if data["score"] >= 80 else "🟡" if data["score"] >= 70 else "🔴"
            print(f"  {status_icon} {category.title()}: {data['score']:.1f}/100")
        
        if self.audit_results["critical_issues"]:
            print("\n🚨 CRITICAL ISSUES:")
            for issue in self.audit_results["critical_issues"]:
                print(f"  ❌ {issue}")
        
        if self.audit_results["warnings"]:
            print("\n⚠️  WARNINGS:")
            for warning in self.audit_results["warnings"]:
                print(f"  ⚠️  {warning}")
        
        print("\n📋 RECOMMENDATIONS:")
        recommendations = [
            "Enable HTTPS in production",
            "Implement proper CORS configuration",
            "Enable rate limiting with Redis",
            "Use strong, unique JWT secret keys",
            "Enable security monitoring",
            "Implement proper input validation",
            "Use secure password policies",
            "Enable database RLS policies",
            "Implement file upload validation",
            "Enable security headers",
            "Use secure session management",
            "Implement proper logging",
            "Regular security audits",
            "Keep dependencies updated",
            "Use environment-specific configurations"
        ]
        
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i:2d}. {rec}")
        
        print(f"\n📄 Full report saved to: security_audit_report.json")
        
        # Save detailed report
        with open("security_audit_report.json", "w") as f:
            json.dump(self.audit_results, f, indent=2, default=str)


async def main():
    """Main audit function"""
    auditor = SecurityAuditor()
    await auditor.run_full_audit()


if __name__ == "__main__":
    asyncio.run(main())
