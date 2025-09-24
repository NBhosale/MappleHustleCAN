#!/usr/bin/env python3
"""
Validation Enforcement Script for MapleHustleCAN
Ensures all schemas use enhanced validation rules
"""

import sys
import ast
from pathlib import Path
from typing import List, Dict, Any
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ValidationEnforcer:
    """Enforces validation rules across all schemas"""
    
    def __init__(self):
        self.project_root = project_root
        self.schemas_dir = project_root / "app" / "schemas"
        self.routers_dir = project_root / "app" / "routers"
        self.issues = []
    
    def check_email_validation(self, file_path: Path) -> List[Dict[str, Any]]:
        """Check if email fields use proper validation"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for item in node.body:
                        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                            if item.target.id == 'email':
                                # Check if using EmailStr
                                if 'EmailStr' not in content:
                                    issues.append({
                                        'file': str(file_path),
                                        'line': item.lineno,
                                        'class': node.name,
                                        'field': 'email',
                                        'issue': 'email_not_using_EmailStr',
                                        'severity': 'warning'
                                    })
                                
                                # Check if using enhanced validation
                                if 'EmailValidation' not in content and 'validate_email' not in content:
                                    issues.append({
                                        'file': str(file_path),
                                        'line': item.lineno,
                                        'class': node.name,
                                        'field': 'email',
                                        'issue': 'email_missing_enhanced_validation',
                                        'severity': 'warning'
                                    })
        
        except Exception as e:
            logger.error(f"Error checking {file_path}: {e}")
        
        return issues
    
    def check_password_validation(self, file_path: Path) -> List[Dict[str, Any]]:
        """Check if password fields use proper validation"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for item in node.body:
                        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                            if item.target.id == 'password':
                                # Check if using proper validation
                                if 'PasswordValidation' not in content and 'validate_password' not in content:
                                    issues.append({
                                        'file': str(file_path),
                                        'line': item.lineno,
                                        'class': node.name,
                                        'field': 'password',
                                        'issue': 'password_missing_enhanced_validation',
                                        'severity': 'warning'
                                    })
        
        except Exception as e:
            logger.error(f"Error checking {file_path}: {e}")
        
        return issues
    
    def check_monetary_validation(self, file_path: Path) -> List[Dict[str, Any]]:
        """Check if monetary fields use proper validation"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            monetary_fields = ['amount', 'price', 'total_amount', 'platform_fee', 'tip', 'cost']
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for item in node.body:
                        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                            if item.target.id in monetary_fields:
                                # Check if using proper validation
                                if 'MoneyValidation' not in content and 'PaymentValidation' not in content:
                                    issues.append({
                                        'file': str(file_path),
                                        'line': item.lineno,
                                        'class': node.name,
                                        'field': item.target.id,
                                        'issue': 'monetary_field_missing_validation',
                                        'severity': 'warning'
                                    })
        
        except Exception as e:
            logger.error(f"Error checking {file_path}: {e}")
        
        return issues
    
    def check_schema_usage_in_routers(self, file_path: Path) -> List[Dict[str, Any]]:
        """Check if routers use proper schemas"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for direct model usage instead of schemas
            if 'response_model=User[^R]' in content:
                issues.append({
                    'file': str(file_path),
                    'line': 0,
                    'class': 'Router',
                    'field': 'response_model',
                    'issue': 'router_using_model_directly',
                    'severity': 'error'
                })
            
            # Check for missing validation imports
            if 'EmailStr' in content and 'from pydantic import' in content:
                if 'EmailValidation' not in content:
                    issues.append({
                        'file': str(file_path),
                        'line': 0,
                        'class': 'Router',
                        'field': 'imports',
                        'issue': 'missing_enhanced_validation_imports',
                        'severity': 'warning'
                    })
        
        except Exception as e:
            logger.error(f"Error checking {file_path}: {e}")
        
        return issues
    
    def validate_all(self) -> Dict[str, Any]:
        """Run all validation checks"""
        logger.info("🔍 Starting validation enforcement...")
        
        all_issues = []
        
        # Check schemas
        for py_file in self.schemas_dir.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
            
            email_issues = self.check_email_validation(py_file)
            password_issues = self.check_password_validation(py_file)
            monetary_issues = self.check_monetary_validation(py_file)
            
            all_issues.extend(email_issues)
            all_issues.extend(password_issues)
            all_issues.extend(monetary_issues)
        
        # Check routers
        for py_file in self.routers_dir.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
            
            router_issues = self.check_schema_usage_in_routers(py_file)
            all_issues.extend(router_issues)
        
        # Categorize issues
        errors = [i for i in all_issues if i.get('severity') == 'error']
        warnings = [i for i in all_issues if i.get('severity') == 'warning']
        
        return {
            'total_issues': len(all_issues),
            'errors': len(errors),
            'warnings': len(warnings),
            'issues': all_issues,
            'status': 'pass' if len(errors) == 0 else 'fail'
        }
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate validation enforcement report"""
        report = []
        report.append("🔍 Validation Enforcement Report")
        report.append("=" * 40)
        report.append(f"Total issues: {results['total_issues']}")
        report.append(f"Errors: {results['errors']}")
        report.append(f"Warnings: {results['warnings']}")
        report.append(f"Status: {results['status'].upper()}")
        report.append("")
        
        if results['errors']:
            report.append("🚨 ERRORS (Must Fix):")
            report.append("-" * 20)
            for issue in results['issues']:
                if issue.get('severity') == 'error':
                    report.append(f"• {issue['issue']}")
                    if 'file' in issue:
                        report.append(f"  File: {issue['file']}")
                    if 'class' in issue:
                        report.append(f"  Class: {issue['class']}")
                    if 'field' in issue:
                        report.append(f"  Field: {issue['field']}")
                    report.append("")
        
        if results['warnings']:
            report.append("⚠️  WARNINGS (Should Fix):")
            report.append("-" * 25)
            for issue in results['issues']:
                if issue.get('severity') == 'warning':
                    report.append(f"• {issue['issue']}")
                    if 'file' in issue:
                        report.append(f"  File: {issue['file']}")
                    if 'class' in issue:
                        report.append(f"  Class: {issue['class']}")
                    if 'field' in issue:
                        report.append(f"  Field: {issue['field']}")
                    report.append("")
        
        if results['status'] == 'pass':
            report.append("✅ All validation rules are properly enforced!")
        
        return "\n".join(report)


def main():
    """Run validation enforcement"""
    enforcer = ValidationEnforcer()
    results = enforcer.validate_all()
    
    report = enforcer.generate_report(results)
    print(report)
    
    # Exit with error code if there are errors
    if results['errors'] > 0:
        logger.error(f"Validation enforcement failed with {results['errors']} errors")
        sys.exit(1)
    else:
        logger.info("Validation enforcement passed")
        sys.exit(0)


if __name__ == "__main__":
    main()
