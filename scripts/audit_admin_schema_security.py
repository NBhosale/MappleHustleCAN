#!/usr/bin/env python3
"""
Admin Schema Security Audit for MapleHustleCAN
Ensures UserAdminResponse never exposes sensitive fields
"""

import sys
import ast
from pathlib import Path
from typing import List, Dict, Set
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AdminSchemaSecurityAudit:
    """Audits admin schema security and usage"""
    
    def __init__(self):
        self.sensitive_fields = {
            'hashed_password',
            'password_hash',
            'verification_token',
            'password_reset_token',
            'password_reset_expires',
            'token_hash',
            'hashed_token',
            'reset_token',
            'verification_code'
        }
        
        self.admin_schemas = [
            'UserAdminResponse',
            'AdminResponse',
            'AdminUserResponse'
        ]
        
        self.violations = []
    
    def audit_schema_definition(self, file_path: Path) -> List[Dict[str, str]]:
        """Audit schema definition for sensitive fields"""
        violations = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    if any(admin_schema in node.name for admin_schema in self.admin_schemas):
                        violations.extend(self._check_admin_class(node, file_path))
            
        except Exception as e:
            logger.error(f"Error auditing {file_path}: {e}")
        
        return violations
    
    def _check_admin_class(self, node: ast.ClassDef, file_path: Path) -> List[Dict[str, str]]:
        """Check admin class for sensitive fields"""
        violations = []
        
        for item in node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                field_name = item.target.id
                
                if field_name in self.sensitive_fields:
                    violations.append({
                        'file': str(file_path),
                        'line': item.lineno,
                        'class': node.name,
                        'field': field_name,
                        'severity': 'critical',
                        'message': f"CRITICAL: Sensitive field '{field_name}' found in admin schema '{node.name}'"
                    })
        
        return violations
    
    def audit_schema_usage(self, file_path: Path) -> List[Dict[str, str]]:
        """Audit how admin schemas are used in routers"""
        violations = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for admin schema usage in response_model
            for admin_schema in self.admin_schemas:
                if f'response_model={admin_schema}' in content:
                    violations.append({
                        'file': str(file_path),
                        'line': 0,
                        'class': 'Router',
                        'field': 'response_model',
                        'severity': 'warning',
                        'message': f"Admin schema '{admin_schema}' used in router - ensure no sensitive data exposure"
                    })
            
            # Check for direct model usage in admin endpoints
            import re
            if 'require_admin' in content and re.search(r'response_model=User[^a-zA-Z]', content):
                violations.append({
                    'file': str(file_path),
                    'line': 0,
                    'class': 'Router',
                    'field': 'response_model',
                    'severity': 'critical',
                    'message': "CRITICAL: Admin endpoint uses User model directly instead of safe schema"
                })
            
        except Exception as e:
            logger.error(f"Error auditing usage in {file_path}: {e}")
        
        return violations
    
    def audit_all_files(self) -> List[Dict[str, str]]:
        """Audit all relevant files"""
        all_violations = []
        
        # Audit schema definitions
        schemas_dir = project_root / "app" / "schemas"
        for py_file in schemas_dir.rglob("*.py"):
            violations = self.audit_schema_definition(py_file)
            all_violations.extend(violations)
        
        # Audit router usage
        routers_dir = project_root / "app" / "routers"
        for py_file in routers_dir.rglob("*.py"):
            violations = self.audit_schema_usage(py_file)
            all_violations.extend(violations)
        
        return all_violations
    
    def generate_report(self, violations: List[Dict[str, str]]) -> str:
        """Generate security audit report"""
        if not violations:
            return "✅ Admin schema security audit passed - no sensitive fields exposed!"
        
        critical_violations = [v for v in violations if v['severity'] == 'critical']
        warning_violations = [v for v in violations if v['severity'] == 'warning']
        
        report = []
        report.append("🔒 Admin Schema Security Audit Report")
        report.append("=" * 50)
        report.append(f"Total violations: {len(violations)}")
        report.append(f"Critical violations: {len(critical_violations)}")
        report.append(f"Warning violations: {len(warning_violations)}")
        report.append("")
        
        if critical_violations:
            report.append("🚨 CRITICAL VIOLATIONS (Must Fix Immediately):")
            report.append("-" * 50)
            for violation in critical_violations:
                report.append(f"File: {violation['file']}")
                report.append(f"Line {violation['line']}: {violation['class']}")
                report.append(f"Field: {violation['field']}")
                report.append(f"Issue: {violation['message']}")
                report.append("")
        
        if warning_violations:
            report.append("⚠️  WARNING VIOLATIONS (Review Required):")
            report.append("-" * 40)
            for violation in warning_violations:
                report.append(f"File: {violation['file']}")
                report.append(f"Issue: {violation['message']}")
                report.append("")
        
        return "\n".join(report)


def main():
    """Run admin schema security audit"""
    logger.info("🔒 Starting admin schema security audit...")
    
    auditor = AdminSchemaSecurityAudit()
    violations = auditor.audit_all_files()
    
    report = auditor.generate_report(violations)
    print(report)
    
    # Exit with error code if critical violations found
    critical_count = len([v for v in violations if v['severity'] == 'critical'])
    if critical_count > 0:
        logger.error(f"Found {critical_count} critical security violations")
        sys.exit(1)
    else:
        logger.info("✅ No critical security violations found")
        sys.exit(0)


if __name__ == "__main__":
    main()
