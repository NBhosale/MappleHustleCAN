#!/usr/bin/env python3
"""
Schema Security Validation Script for MapleHustleCAN
Ensures no sensitive fields are exposed in response schemas
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


class SchemaSecurityValidator:
    """Validates that response schemas don't expose sensitive fields"""
    
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
        
        self.response_schema_patterns = [
            'Response',
            'AdminResponse',
            'PublicResponse',
            'ClientResponse'
        ]
        
        self.violations = []
    
    def check_file(self, file_path: Path) -> List[Dict[str, str]]:
        """Check a single Python file for schema security violations"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            violations = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    violations.extend(self._check_class(node, file_path))
            
            return violations
            
        except Exception as e:
            logger.error(f"Error checking {file_path}: {e}")
            return []
    
    def _check_class(self, node: ast.ClassDef, file_path: Path) -> List[Dict[str, str]]:
        """Check a class definition for security violations"""
        violations = []
        
        # Check if this is a response schema
        is_response_schema = any(pattern in node.name for pattern in self.response_schema_patterns)
        
        if not is_response_schema:
            return violations
        
        # Check for sensitive fields in class body
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
                        'message': f"Sensitive field '{field_name}' found in response schema '{node.name}'"
                    })
        
        return violations
    
    def check_directory(self, directory: Path) -> List[Dict[str, str]]:
        """Check all Python files in a directory"""
        all_violations = []
        
        for py_file in directory.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            
            violations = self.check_file(py_file)
            all_violations.extend(violations)
        
        return all_violations
    
    def generate_report(self, violations: List[Dict[str, str]]) -> str:
        """Generate a security validation report"""
        if not violations:
            return "✅ All response schemas are secure - no sensitive fields exposed!"
        
        # Group violations by severity
        critical_violations = [v for v in violations if v['severity'] == 'critical']
        
        report = []
        report.append("🔒 Schema Security Validation Report")
        report.append("=" * 50)
        report.append(f"Total violations found: {len(violations)}")
        report.append(f"Critical violations: {len(critical_violations)}")
        report.append("")
        
        if critical_violations:
            report.append("🚨 CRITICAL VIOLATIONS (Must Fix):")
            report.append("-" * 40)
            
            for violation in critical_violations:
                report.append(f"File: {violation['file']}")
                report.append(f"Line {violation['line']}: {violation['class']}")
                report.append(f"Field: {violation['field']}")
                report.append(f"Issue: {violation['message']}")
                report.append("")
        
        return "\n".join(report)
    
    def validate_schema_imports(self, file_path: Path) -> List[Dict[str, str]]:
        """Validate that schemas are properly imported and used"""
        violations = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for direct model usage in routers
            if 'routers' in str(file_path):
                if 'from app.models.users import User' in content:
                    # Check if User model is used in response_model
                    if 'response_model=User' in content:
                        violations.append({
                            'file': str(file_path),
                            'line': 0,
                            'class': 'Router',
                            'field': 'response_model',
                            'severity': 'warning',
                            'message': "Router uses User model directly instead of UserResponse schema"
                        })
            
        except Exception as e:
            logger.error(f"Error validating imports in {file_path}: {e}")
        
        return violations


def main():
    """Run schema security validation"""
    logger.info("🔒 Starting schema security validation...")
    
    validator = SchemaSecurityValidator()
    
    # Check schemas directory
    schemas_dir = project_root / "app" / "schemas"
    violations = validator.check_directory(schemas_dir)
    
    # Check routers directory for improper model usage
    routers_dir = project_root / "app" / "routers"
    router_violations = []
    for py_file in routers_dir.rglob("*.py"):
        router_violations.extend(validator.validate_schema_imports(py_file))
    
    all_violations = violations + router_violations
    
    # Generate report
    report = validator.generate_report(all_violations)
    print(report)
    
    # Exit with error code if violations found
    if all_violations:
        critical_count = len([v for v in all_violations if v['severity'] == 'critical'])
        if critical_count > 0:
            logger.error(f"Found {critical_count} critical security violations")
            sys.exit(1)
        else:
            logger.warning(f"Found {len(all_violations)} security warnings")
            sys.exit(0)
    else:
        logger.info("✅ No security violations found")
        sys.exit(0)


if __name__ == "__main__":
    main()
