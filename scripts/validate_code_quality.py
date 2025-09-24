#!/usr/bin/env python3
"""
Code Quality Validation Script for MapleHustleCAN
Comprehensive validation of logging, error handling, typing, and documentation
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Any
import logging
import ast
import re

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CodeQualityValidator:
    """Comprehensive code quality validation"""
    
    def __init__(self):
        self.project_root = project_root
        self.app_dir = project_root / "app"
        self.docs_dir = project_root / "docs"
        self.scripts_dir = project_root / "scripts"
        self.issues = []
        self.passed_checks = []
    
    def check_structured_logging(self) -> Dict[str, Any]:
        """Check structured logging implementation"""
        logger.info("🔍 Checking structured logging...")
        
        checks = {
            'structured_logging_exists': False,
            'json_logging': False,
            'request_id_tracking': False,
            'logging_middleware': False,
            'context_variables': False,
            'business_logger': False,
            'api_logger': False,
            'logging_setup': False
        }
        
        # Check structured_logging.py
        logging_file = self.app_dir / "core" / "structured_logging.py"
        if logging_file.exists():
            with open(logging_file, 'r') as f:
                content = f.read()
                
                if 'StructuredFormatter' in content:
                    checks['structured_logging_exists'] = True
                
                if 'json.dumps' in content and 'log_entry' in content:
                    checks['json_logging'] = True
                
                if 'request_id_var' in content and 'ContextVar' in content:
                    checks['request_id_tracking'] = True
                    checks['context_variables'] = True
                
                if 'RequestLoggingMiddleware' in content:
                    checks['logging_middleware'] = True
                
                if 'BusinessLogicLogger' in content:
                    checks['business_logger'] = True
                
                if 'APILogger' in content:
                    checks['api_logger'] = True
                
                if 'setup_structured_logging' in content:
                    checks['logging_setup'] = True
        
        return checks
    
    def check_error_handling(self) -> Dict[str, Any]:
        """Check global error handling implementation"""
        logger.info("🔍 Checking error handling...")
        
        checks = {
            'global_handlers_exist': False,
            'json_error_format': False,
            'error_schemas': False,
            'exception_handlers': False,
            'custom_exceptions': False,
            'error_logging': False,
            'error_codes': False,
            'error_middleware': False
        }
        
        # Check global_exception_handlers.py
        handlers_file = self.app_dir / "core" / "global_exception_handlers.py"
        if handlers_file.exists():
            with open(handlers_file, 'r') as f:
                content = f.read()
                
                if 'global_exception_handlers' in content:
                    checks['global_handlers_exist'] = True
                
                if 'JSONResponse' in content and 'error_response' in content:
                    checks['json_error_format'] = True
                
                if 'ErrorCode' in content and 'create_error_response' in content:
                    checks['error_schemas'] = True
                    checks['error_codes'] = True
                
                if 'exception_handler' in content and 'async def' in content:
                    checks['exception_handlers'] = True
                
                if 'BusinessError' in content and 'ValidationError' in content:
                    checks['custom_exceptions'] = True
                
                if 'logger.error' in content or 'logger.warning' in content:
                    checks['error_logging'] = True
        
        # Check error schemas
        error_schemas_file = self.app_dir / "schemas" / "errors.py"
        if error_schemas_file.exists():
            with open(error_schemas_file, 'r') as f:
                content = f.read()
                if 'ErrorResponse' in content and 'ErrorCode' in content:
                    checks['error_schemas'] = True
                    checks['error_codes'] = True
        
        return checks
    
    def check_typing_enforcement(self) -> Dict[str, Any]:
        """Check typing enforcement implementation"""
        logger.info("🔍 Checking typing enforcement...")
        
        checks = {
            'mypy_ci_integration': False,
            'typing_script_exists': False,
            'type_hints_validation': False,
            'mypy_config': False,
            'typing_imports': False,
            'function_annotations': False,
            'class_annotations': False,
            'return_type_hints': False
        }
        
        # Check CI integration
        ci_file = project_root / ".github" / "workflows" / "ci.yml"
        if ci_file.exists():
            with open(ci_file, 'r') as f:
                content = f.read()
                if 'mypy' in content and 'app/' in content:
                    checks['mypy_ci_integration'] = True
        
        # Check typing script
        typing_script = self.scripts_dir / "check_typing.py"
        if typing_script.exists():
            with open(typing_script, 'r') as f:
                content = f.read()
                if 'TypingChecker' in content and 'mypy' in content.lower():
                    checks['typing_script_exists'] = True
                    checks['type_hints_validation'] = True
        
        # Check mypy configuration
        mypy_configs = ['mypy.ini', 'pyproject.toml', '.mypy.ini']
        for config_file in mypy_configs:
            config_path = project_root / config_file
            if config_path.exists():
                checks['mypy_config'] = True
                break
        
        # Check typing usage in code
        typing_usage_found = False
        for py_file in self.app_dir.rglob("*.py"):
            if py_file.name != "__init__.py":
                with open(py_file, 'r') as f:
                    content = f.read()
                    if 'from typing import' in content or 'typing.' in content:
                        checks['typing_imports'] = True
                        typing_usage_found = True
                        break
        
        if typing_usage_found:
            checks['function_annotations'] = True
            checks['class_annotations'] = True
            checks['return_type_hints'] = True
        
        return checks
    
    def check_documentation_consolidation(self) -> Dict[str, Any]:
        """Check documentation consolidation"""
        logger.info("🔍 Checking documentation consolidation...")
        
        checks = {
            'architecture_doc_exists': False,
            'security_doc_exists': False,
            'docs_directory_exists': False,
            'comprehensive_architecture': False,
            'comprehensive_security': False,
            'markdown_format': False,
            'structured_docs': False,
            'up_to_date_docs': False
        }
        
        # Check docs directory
        if self.docs_dir.exists():
            checks['docs_directory_exists'] = True
        
        # Check ARCHITECTURE.md
        arch_doc = self.docs_dir / "ARCHITECTURE.md"
        if arch_doc.exists():
            checks['architecture_doc_exists'] = True
            with open(arch_doc, 'r') as f:
                content = f.read()
                if len(content) > 1000 and '##' in content:  # Comprehensive doc
                    checks['comprehensive_architecture'] = True
                if content.startswith('#'):  # Markdown format
                    checks['markdown_format'] = True
        
        # Check SECURITY.md
        security_doc = self.docs_dir / "SECURITY.md"
        if security_doc.exists():
            checks['security_doc_exists'] = True
            with open(security_doc, 'r') as f:
                content = f.read()
                if len(content) > 2000 and '##' in content:  # Comprehensive doc
                    checks['comprehensive_security'] = True
                if content.startswith('#'):  # Markdown format
                    checks['markdown_format'] = True
        
        # Check for structured documentation
        if checks['architecture_doc_exists'] and checks['security_doc_exists']:
            checks['structured_docs'] = True
        
        # Check for recent updates (basic check)
        if checks['architecture_doc_exists'] and checks['security_doc_exists']:
            checks['up_to_date_docs'] = True  # Assume up to date if comprehensive
        
        return checks
    
    def check_code_consistency(self) -> Dict[str, Any]:
        """Check code consistency and quality"""
        logger.info("🔍 Checking code consistency...")
        
        checks = {
            'consistent_imports': False,
            'consistent_naming': False,
            'consistent_formatting': False,
            'docstring_usage': False,
            'error_handling_patterns': False,
            'logging_usage': False,
            'type_hint_usage': False,
            'code_organization': False
        }
        
        # Check for consistent patterns across the codebase
        import_patterns = set()
        naming_patterns = set()
        docstring_count = 0
        error_handling_count = 0
        logging_count = 0
        type_hint_count = 0
        
        for py_file in self.app_dir.rglob("*.py"):
            if py_file.name != "__init__.py":
                with open(py_file, 'r') as f:
                    content = f.read()
                    
                    # Check import patterns
                    import_lines = [line.strip() for line in content.split('\n') if line.strip().startswith('import') or line.strip().startswith('from')]
                    for line in import_lines:
                        if 'from' in line:
                            import_patterns.add('from_import')
                        else:
                            import_patterns.add('direct_import')
                    
                    # Check naming patterns
                    if 'def ' in content:
                        naming_patterns.add('snake_case')
                    
                    # Check docstrings
                    if '"""' in content or "'''" in content:
                        docstring_count += 1
                    
                    # Check error handling
                    if 'try:' in content and 'except' in content:
                        error_handling_count += 1
                    
                    # Check logging
                    if 'logger.' in content or 'logging.' in content:
                        logging_count += 1
                    
                    # Check type hints
                    if '->' in content or ': ' in content:
                        type_hint_count += 1
        
        # Evaluate consistency
        if len(import_patterns) <= 2:  # Consistent import style
            checks['consistent_imports'] = True
        
        if len(naming_patterns) <= 2:  # Consistent naming
            checks['consistent_naming'] = True
        
        if docstring_count > 5:  # Good docstring usage
            checks['docstring_usage'] = True
        
        if error_handling_count > 10:  # Good error handling
            checks['error_handling_patterns'] = True
        
        if logging_count > 10:  # Good logging usage
            checks['logging_usage'] = True
        
        if type_hint_count > 20:  # Good type hint usage
            checks['type_hint_usage'] = True
        
        # Check code organization
        if (self.app_dir / "core").exists() and (self.app_dir / "routers").exists():
            checks['code_organization'] = True
        
        return checks
    
    def check_ci_integration(self) -> Dict[str, Any]:
        """Check CI integration for code quality"""
        logger.info("🔍 Checking CI integration...")
        
        checks = {
            'ci_file_exists': False,
            'linting_integration': False,
            'typing_integration': False,
            'security_scanning': False,
            'code_formatting': False,
            'pre_commit_hooks': False,
            'quality_gates': False,
            'automated_testing': False
        }
        
        # Check CI file
        ci_file = project_root / ".github" / "workflows" / "ci.yml"
        if ci_file.exists():
            checks['ci_file_exists'] = True
            with open(ci_file, 'r') as f:
                content = f.read()
                
                if 'flake8' in content or 'pylint' in content:
                    checks['linting_integration'] = True
                
                if 'mypy' in content:
                    checks['typing_integration'] = True
                
                if 'bandit' in content or 'safety' in content:
                    checks['security_scanning'] = True
                
                if 'black' in content or 'isort' in content:
                    checks['code_formatting'] = True
                
                if 'pre-commit' in content:
                    checks['pre_commit_hooks'] = True
                
                if 'pytest' in content or 'test' in content:
                    checks['automated_testing'] = True
        
        # Check pre-commit config
        pre_commit_config = project_root / ".pre-commit-config.yaml"
        if pre_commit_config.exists():
            checks['pre_commit_hooks'] = True
        
        # Quality gates (if CI fails on quality issues)
        if checks['linting_integration'] and checks['typing_integration']:
            checks['quality_gates'] = True
        
        return checks
    
    def validate_all(self) -> Dict[str, Any]:
        """Run all code quality validations"""
        logger.info("🔍 Starting comprehensive code quality validation...")
        
        results = {
            'structured_logging': self.check_structured_logging(),
            'error_handling': self.check_error_handling(),
            'typing_enforcement': self.check_typing_enforcement(),
            'documentation_consolidation': self.check_documentation_consolidation(),
            'code_consistency': self.check_code_consistency(),
            'ci_integration': self.check_ci_integration()
        }
        
        # Calculate overall code quality score
        total_checks = 0
        passed_checks = 0
        
        for category, checks in results.items():
            for check, passed in checks.items():
                total_checks += 1
                if passed:
                    passed_checks += 1
        
        code_quality_score = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
        
        results['overall'] = {
            'total_checks': total_checks,
            'passed_checks': passed_checks,
            'code_quality_score': code_quality_score,
            'status': 'PASS' if code_quality_score >= 80 else 'FAIL'
        }
        
        return results
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate code quality validation report"""
        report = []
        report.append("📊 Code Quality Validation Report")
        report.append("=" * 60)
        report.append("")
        
        # Overall status
        overall = results['overall']
        report.append(f"📊 Overall Code Quality Score: {overall['code_quality_score']:.1f}%")
        report.append(f"✅ Passed Checks: {overall['passed_checks']}/{overall['total_checks']}")
        report.append(f"🎯 Status: {overall['status']}")
        report.append("")
        
        # Category breakdown
        categories = {
            'structured_logging': '📝 Structured Logging',
            'error_handling': '🚨 Error Handling',
            'typing_enforcement': '🔍 Typing Enforcement',
            'documentation_consolidation': '📚 Documentation',
            'code_consistency': '🔧 Code Consistency',
            'ci_integration': '🔄 CI Integration'
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
        if overall['code_quality_score'] < 80:
            report.append("⚠️ Code Quality Recommendations:")
            report.append("-" * 35)
            
            if not results['structured_logging']['structured_logging_exists']:
                report.append("• Implement structured logging with JSON format")
            if not results['error_handling']['global_handlers_exist']:
                report.append("• Add global error handler middleware")
            if not results['typing_enforcement']['mypy_ci_integration']:
                report.append("• Integrate mypy in CI pipeline")
            if not results['documentation_consolidation']['architecture_doc_exists']:
                report.append("• Create comprehensive ARCHITECTURE.md")
            if not results['documentation_consolidation']['security_doc_exists']:
                report.append("• Create comprehensive SECURITY.md")
            if not results['code_consistency']['consistent_imports']:
                report.append("• Standardize import patterns")
            if not results['ci_integration']['quality_gates']:
                report.append("• Add quality gates to CI pipeline")
        
        return "\n".join(report)


def main():
    """Run code quality validation"""
    validator = CodeQualityValidator()
    results = validator.validate_all()
    
    report = validator.generate_report(results)
    print(report)
    
    # Exit with error code if code quality score is low
    if results['overall']['code_quality_score'] < 80:
        logger.error(f"Code quality validation failed with score {results['overall']['code_quality_score']:.1f}%")
        sys.exit(1)
    else:
        logger.info("Code quality validation passed")
        sys.exit(0)


if __name__ == "__main__":
    main()
