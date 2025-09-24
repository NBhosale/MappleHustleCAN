#!/usr/bin/env python3
"""
Security Validation Script for MapleHustleCAN
Comprehensive security audit and validation
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Any
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SecurityValidator:
    """Comprehensive security validation"""
    
    def __init__(self):
        self.project_root = project_root
        self.issues = []
        self.passed_checks = []
    
    def check_jwt_refresh_tokens(self) -> Dict[str, Any]:
        """Check JWT refresh token implementation"""
        logger.info("🔐 Checking JWT refresh token implementation...")
        
        checks = {
            'refresh_token_manager_exists': False,
            'refresh_token_model_exists': False,
            'refresh_token_rotation': False,
            'refresh_token_storage': False,
            'auth_router_integration': False
        }
        
        # Check refresh token manager
        manager_path = project_root / "app" / "core" / "refresh_token_manager.py"
        if manager_path.exists():
            checks['refresh_token_manager_exists'] = True
            with open(manager_path, 'r') as f:
                content = f.read()
                if 'rotate_refresh_token' in content:
                    checks['refresh_token_rotation'] = True
                if 'create_refresh_token' in content:
                    checks['refresh_token_storage'] = True
        
        # Check refresh token model
        model_path = project_root / "app" / "models" / "tokens.py"
        if model_path.exists():
            checks['refresh_token_model_exists'] = True
        
        # Check auth router integration
        auth_path = project_root / "app" / "routers" / "auth.py"
        if auth_path.exists():
            with open(auth_path, 'r') as f:
                content = f.read()
                if 'refresh_token_manager' in content and 'rotate_refresh_token' in content:
                    checks['auth_router_integration'] = True
        
        return checks
    
    def check_security_headers(self) -> Dict[str, Any]:
        """Check security headers implementation"""
        logger.info("🛡️ Checking security headers implementation...")
        
        checks = {
            'middleware_exists': False,
            'x_frame_options': False,
            'csp_header': False,
            'hsts_header': False,
            'additional_headers': False
        }
        
        middleware_path = project_root / "app" / "core" / "middleware.py"
        if middleware_path.exists():
            checks['middleware_exists'] = True
            with open(middleware_path, 'r') as f:
                content = f.read()
                if 'X-Frame-Options' in content:
                    checks['x_frame_options'] = True
                if 'Content-Security-Policy' in content:
                    checks['csp_header'] = True
                if 'Strict-Transport-Security' in content:
                    checks['hsts_header'] = True
                if 'X-Content-Type-Options' in content and 'X-XSS-Protection' in content:
                    checks['additional_headers'] = True
        
        return checks
    
    def check_rate_limiting(self) -> Dict[str, Any]:
        """Check rate limiting implementation"""
        logger.info("⏱️ Checking rate limiting implementation...")
        
        checks = {
            'slowapi_imported': False,
            'limiter_configured': False,
            'auth_endpoints_limited': False,
            'rate_limit_handler': False
        }
        
        # Check middleware
        middleware_path = project_root / "app" / "core" / "middleware.py"
        if middleware_path.exists():
            with open(middleware_path, 'r') as f:
                content = f.read()
                if 'slowapi' in content and 'Limiter' in content:
                    checks['slowapi_imported'] = True
                if 'limiter = Limiter' in content:
                    checks['limiter_configured'] = True
                if 'rate_limit_exceeded_handler' in content:
                    checks['rate_limit_handler'] = True
        
        # Check auth router
        auth_path = project_root / "app" / "routers" / "auth.py"
        if auth_path.exists():
            with open(auth_path, 'r') as f:
                content = f.read()
                if '@limiter.limit' in content and 'login' in content and 'register' in content:
                    checks['auth_endpoints_limited'] = True
        
        return checks
    
    def check_row_level_security(self) -> Dict[str, Any]:
        """Check Row-Level Security implementation"""
        logger.info("🔒 Checking Row-Level Security implementation...")
        
        checks = {
            'rls_module_exists': False,
            'rls_migration_exists': False,
            'rls_policies_defined': False,
            'rls_middleware': False
        }
        
        # Check RLS module
        rls_path = project_root / "app" / "core" / "row_level_security.py"
        if rls_path.exists():
            checks['rls_module_exists'] = True
            with open(rls_path, 'r') as f:
                content = f.read()
                if 'CREATE POLICY' in content and 'ENABLE ROW LEVEL SECURITY' in content:
                    checks['rls_policies_defined'] = True
                if 'RLSMiddleware' in content:
                    checks['rls_middleware'] = True
        
        # Check RLS migration
        migrations_dir = project_root / "alembic" / "versions"
        if migrations_dir.exists():
            for migration_file in migrations_dir.glob("*.py"):
                if 'row_level_security' in migration_file.name or 'rls' in migration_file.name:
                    checks['rls_migration_exists'] = True
                    break
        
        return checks
    
    def check_password_security(self) -> Dict[str, Any]:
        """Check password security implementation"""
        logger.info("🔑 Checking password security implementation...")
        
        checks = {
            'password_hashing': False,
            'password_validation': False,
            'bcrypt_used': False,
            'password_strength': False
        }
        
        # Check hashing utility
        hashing_path = project_root / "app" / "utils" / "hashing.py"
        if hashing_path.exists():
            with open(hashing_path, 'r') as f:
                content = f.read()
                if 'bcrypt' in content and 'hash_password' in content:
                    checks['password_hashing'] = True
                    checks['bcrypt_used'] = True
        
        # Check validation
        validation_path = project_root / "app" / "schemas" / "validation_enhanced.py"
        if validation_path.exists():
            with open(validation_path, 'r') as f:
                content = f.read()
                if 'PasswordValidation' in content and 'validate_password_strength' in content:
                    checks['password_validation'] = True
                    checks['password_strength'] = True
        
        return checks
    
    def check_sql_injection_protection(self) -> Dict[str, Any]:
        """Check SQL injection protection"""
        logger.info("💉 Checking SQL injection protection...")
        
        checks = {
            'sqlalchemy_orm_used': False,
            'parameterized_queries': False,
            'no_raw_sql': False,
            'input_validation': False
        }
        
        # Check repositories for SQLAlchemy usage
        repos_dir = project_root / "app" / "repositories"
        if repos_dir.exists():
            for repo_file in repos_dir.glob("*.py"):
                with open(repo_file, 'r') as f:
                    content = f.read()
                    if 'from sqlalchemy.orm' in content and 'Session' in content:
                        checks['sqlalchemy_orm_used'] = True
                    if 'query(' in content and 'filter(' in content:
                        checks['parameterized_queries'] = True
                    if 'execute(' not in content or 'text(' not in content:
                        checks['no_raw_sql'] = True
        
        # Check validation
        validation_path = project_root / "app" / "schemas" / "validation_enhanced.py"
        if validation_path.exists():
            checks['input_validation'] = True
        
        return checks
    
    def validate_all(self) -> Dict[str, Any]:
        """Run all security validations"""
        logger.info("🔍 Starting comprehensive security validation...")
        
        results = {
            'jwt_refresh_tokens': self.check_jwt_refresh_tokens(),
            'security_headers': self.check_security_headers(),
            'rate_limiting': self.check_rate_limiting(),
            'row_level_security': self.check_row_level_security(),
            'password_security': self.check_password_security(),
            'sql_injection_protection': self.check_sql_injection_protection()
        }
        
        # Calculate overall security score
        total_checks = 0
        passed_checks = 0
        
        for category, checks in results.items():
            for check, passed in checks.items():
                total_checks += 1
                if passed:
                    passed_checks += 1
        
        security_score = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
        
        results['overall'] = {
            'total_checks': total_checks,
            'passed_checks': passed_checks,
            'security_score': security_score,
            'status': 'PASS' if security_score >= 80 else 'FAIL'
        }
        
        return results
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate security validation report"""
        report = []
        report.append("🔐 Security Validation Report")
        report.append("=" * 50)
        report.append("")
        
        # Overall status
        overall = results['overall']
        report.append(f"📊 Overall Security Score: {overall['security_score']:.1f}%")
        report.append(f"✅ Passed Checks: {overall['passed_checks']}/{overall['total_checks']}")
        report.append(f"🎯 Status: {overall['status']}")
        report.append("")
        
        # Category breakdown
        categories = {
            'jwt_refresh_tokens': '🔐 JWT Refresh Tokens',
            'security_headers': '🛡️ Security Headers',
            'rate_limiting': '⏱️ Rate Limiting',
            'row_level_security': '🔒 Row-Level Security',
            'password_security': '🔑 Password Security',
            'sql_injection_protection': '💉 SQL Injection Protection'
        }
        
        for category, title in categories.items():
            if category in results:
                report.append(f"{title}:")
                checks = results[category]
                passed = sum(1 for v in checks.values() if v)
                total = len(checks)
                score = (passed / total) * 100 if total > 0 else 0
                report.append(f"  Score: {score:.1f}% ({passed}/{total})")
                
                for check, passed in checks.items():
                    status = "✅" if passed else "❌"
                    check_name = check.replace('_', ' ').title()
                    report.append(f"    {status} {check_name}")
                report.append("")
        
        # Recommendations
        if overall['security_score'] < 80:
            report.append("⚠️ Security Recommendations:")
            report.append("-" * 30)
            
            if not results['jwt_refresh_tokens']['refresh_token_rotation']:
                report.append("• Implement refresh token rotation")
            if not results['security_headers']['csp_header']:
                report.append("• Add Content Security Policy headers")
            if not results['rate_limiting']['auth_endpoints_limited']:
                report.append("• Add rate limiting to authentication endpoints")
            if not results['row_level_security']['rls_policies_defined']:
                report.append("• Implement Row-Level Security policies")
            if not results['password_security']['password_strength']:
                report.append("• Enhance password strength validation")
            if not results['sql_injection_protection']['parameterized_queries']:
                report.append("• Ensure all queries use parameterized statements")
        
        return "\n".join(report)


def main():
    """Run security validation"""
    validator = SecurityValidator()
    results = validator.validate_all()
    
    report = validator.generate_report(results)
    print(report)
    
    # Exit with error code if security score is low
    if results['overall']['security_score'] < 80:
        logger.error(f"Security validation failed with score {results['overall']['security_score']:.1f}%")
        sys.exit(1)
    else:
        logger.info("Security validation passed")
        sys.exit(0)


if __name__ == "__main__":
    main()
