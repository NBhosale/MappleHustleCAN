#!/usr/bin/env python3
"""
Testing & CI/CD Validation Script for MapleHustleCAN
Comprehensive validation of test coverage and CI/CD pipeline
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


class TestingValidator:
    """Comprehensive testing and CI/CD validation"""
    
    def __init__(self):
        self.project_root = project_root
        self.tests_dir = project_root / "tests"
        self.ci_file = project_root / ".github" / "workflows" / "ci.yml"
        self.precommit_file = project_root / ".pre-commit-config.yaml"
        self.issues = []
        self.passed_checks = []
    
    def check_test_coverage(self) -> Dict[str, Any]:
        """Check test coverage completeness"""
        logger.info("🧪 Checking test coverage...")
        
        checks = {
            'test_files_exist': False,
            'router_tests_complete': False,
            'integration_tests_exist': False,
            'migration_tests_exist': False,
            'security_tests_exist': False,
            'validation_tests_exist': False,
            'load_tests_exist': False
        }
        
        # Check if tests directory exists
        if self.tests_dir.exists():
            checks['test_files_exist'] = True
            
            # Get all test files
            test_files = list(self.tests_dir.glob("test_*.py"))
            test_names = [f.stem for f in test_files]
            
            # Check for router tests
            router_tests = [
                'test_users', 'test_services', 'test_bookings', 'test_items',
                'test_orders', 'test_payments', 'test_messages', 'test_notifications',
                'test_auth', 'test_provinces', 'test_search', 'test_health', 'test_files'
            ]
            
            missing_router_tests = []
            for router_test in router_tests:
                if router_test not in test_names:
                    missing_router_tests.append(router_test)
            
            if not missing_router_tests:
                checks['router_tests_complete'] = True
            
            # Check for specific test types
            if 'test_integration' in test_names:
                checks['integration_tests_exist'] = True
            
            if 'test_migrations' in test_names:
                checks['migration_tests_exist'] = True
            
            if 'test_security' in test_names:
                checks['security_tests_exist'] = True
            
            if 'test_validation' in test_names:
                checks['validation_tests_exist'] = True
            
            if 'test_load' in test_names or 'load_test' in test_names:
                checks['load_tests_exist'] = True
        
        return checks
    
    def check_ci_pipeline(self) -> Dict[str, Any]:
        """Check CI/CD pipeline configuration"""
        logger.info("🔄 Checking CI/CD pipeline...")
        
        checks = {
            'ci_file_exists': False,
            'test_job_exists': False,
            'migration_tests': False,
            'precommit_enforced': False,
            'security_scanning': False,
            'load_testing': False,
            'coverage_reporting': False,
            'docker_build': False
        }
        
        if self.ci_file.exists():
            checks['ci_file_exists'] = True
            
            with open(self.ci_file, 'r') as f:
                ci_content = f.read()
            
            # Check for test job
            if 'jobs:' in ci_content and 'test:' in ci_content:
                checks['test_job_exists'] = True
            
            # Check for migration tests
            if 'alembic upgrade head' in ci_content and 'alembic downgrade base' in ci_content:
                checks['migration_tests'] = True
            
            # Check for pre-commit enforcement
            if 'pre-commit run --all-files' in ci_content:
                checks['precommit_enforced'] = True
            
            # Check for security scanning
            if 'security-scan' in ci_content and 'bandit' in ci_content:
                checks['security_scanning'] = True
            
            # Check for load testing
            if 'load-test' in ci_content and 'locust' in ci_content:
                checks['load_testing'] = True
            
            # Check for coverage reporting
            if '--cov=' in ci_content and 'codecov' in ci_content:
                checks['coverage_reporting'] = True
            
            # Check for Docker build
            if 'docker/build-push-action' in ci_content:
                checks['docker_build'] = True
        
        return checks
    
    def check_precommit_hooks(self) -> Dict[str, Any]:
        """Check pre-commit hooks configuration"""
        logger.info("🔧 Checking pre-commit hooks...")
        
        checks = {
            'precommit_file_exists': False,
            'black_configured': False,
            'flake8_configured': False,
            'mypy_configured': False,
            'isort_configured': False,
            'bandit_configured': False,
            'safety_configured': False,
            'pylint_configured': False
        }
        
        if self.precommit_file.exists():
            checks['precommit_file_exists'] = True
            
            with open(self.precommit_file, 'r') as f:
                precommit_content = f.read()
            
            # Check for specific tools
            if 'black' in precommit_content:
                checks['black_configured'] = True
            
            if 'flake8' in precommit_content:
                checks['flake8_configured'] = True
            
            if 'mypy' in precommit_content:
                checks['mypy_configured'] = True
            
            if 'isort' in precommit_content:
                checks['isort_configured'] = True
            
            if 'bandit' in precommit_content:
                checks['bandit_configured'] = True
            
            if 'safety' in precommit_content:
                checks['safety_configured'] = True
            
            if 'pylint' in precommit_content:
                checks['pylint_configured'] = True
        
        return checks
    
    def check_test_quality(self) -> Dict[str, Any]:
        """Check test quality and structure"""
        logger.info("📊 Checking test quality...")
        
        checks = {
            'conftest_exists': False,
            'factories_exist': False,
            'test_imports_valid': False,
            'test_structure_valid': False,
            'fixtures_defined': False
        }
        
        # Check for conftest.py
        conftest_file = self.tests_dir / "conftest.py"
        if conftest_file.exists():
            checks['conftest_exists'] = True
            
            with open(conftest_file, 'r') as f:
                conftest_content = f.read()
            
            # Check for fixtures
            if '@pytest.fixture' in conftest_content:
                checks['fixtures_defined'] = True
        
        # Check for factories
        factories_file = self.tests_dir / "factories.py"
        if factories_file.exists():
            checks['factories_exist'] = True
        
        # Check test structure
        if self.tests_dir.exists():
            test_files = list(self.tests_dir.glob("test_*.py"))
            if len(test_files) > 0:
                checks['test_structure_valid'] = True
                
                # Check for valid imports in test files
                valid_imports = True
                for test_file in test_files[:3]:  # Check first 3 files
                    try:
                        with open(test_file, 'r') as f:
                            content = f.read()
                            if 'import pytest' in content or 'from fastapi.testclient import TestClient' in content:
                                continue
                            else:
                                valid_imports = False
                                break
                    except Exception:
                        valid_imports = False
                        break
                
                checks['test_imports_valid'] = valid_imports
        
        return checks
    
    def check_migration_testing(self) -> Dict[str, Any]:
        """Check migration testing implementation"""
        logger.info("🗄️ Checking migration testing...")
        
        checks = {
            'migration_tests_exist': False,
            'upgrade_downgrade_tests': False,
            'data_integrity_tests': False,
            'reversibility_tests': False,
            'migration_validation_script': False
        }
        
        # Check migration test file
        migration_test_file = self.tests_dir / "test_migrations.py"
        if migration_test_file.exists():
            checks['migration_tests_exist'] = True
            
            with open(migration_test_file, 'r') as f:
                migration_content = f.read()
            
            # Check for specific test methods
            if 'test_migration_upgrade_downgrade_cycle' in migration_content:
                checks['upgrade_downgrade_tests'] = True
            
            if 'test_migration_data_preservation' in migration_content:
                checks['data_integrity_tests'] = True
            
            if 'test_migration_reversibility' in migration_content or 'downgrade' in migration_content:
                checks['reversibility_tests'] = True
        
        # Check for migration validation script
        migration_script = self.project_root / "scripts" / "validate_migrations.py"
        if migration_script.exists():
            checks['migration_validation_script'] = True
        
        return checks
    
    def validate_all(self) -> Dict[str, Any]:
        """Run all testing validations"""
        logger.info("🔍 Starting comprehensive testing validation...")
        
        results = {
            'test_coverage': self.check_test_coverage(),
            'ci_pipeline': self.check_ci_pipeline(),
            'precommit_hooks': self.check_precommit_hooks(),
            'test_quality': self.check_test_quality(),
            'migration_testing': self.check_migration_testing()
        }
        
        # Calculate overall testing score
        total_checks = 0
        passed_checks = 0
        
        for category, checks in results.items():
            for check, passed in checks.items():
                total_checks += 1
                if passed:
                    passed_checks += 1
        
        testing_score = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
        
        results['overall'] = {
            'total_checks': total_checks,
            'passed_checks': passed_checks,
            'testing_score': testing_score,
            'status': 'PASS' if testing_score >= 80 else 'FAIL'
        }
        
        return results
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate testing validation report"""
        report = []
        report.append("🧪 Testing & CI/CD Validation Report")
        report.append("=" * 50)
        report.append("")
        
        # Overall status
        overall = results['overall']
        report.append(f"📊 Overall Testing Score: {overall['testing_score']:.1f}%")
        report.append(f"✅ Passed Checks: {overall['passed_checks']}/{overall['total_checks']}")
        report.append(f"🎯 Status: {overall['status']}")
        report.append("")
        
        # Category breakdown
        categories = {
            'test_coverage': '🧪 Test Coverage',
            'ci_pipeline': '🔄 CI/CD Pipeline',
            'precommit_hooks': '🔧 Pre-commit Hooks',
            'test_quality': '📊 Test Quality',
            'migration_testing': '🗄️ Migration Testing'
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
        if overall['testing_score'] < 80:
            report.append("⚠️ Testing Recommendations:")
            report.append("-" * 30)
            
            if not results['test_coverage']['router_tests_complete']:
                report.append("• Add missing router tests")
            if not results['migration_testing']['upgrade_downgrade_tests']:
                report.append("• Add migration upgrade/downgrade tests")
            if not results['ci_pipeline']['precommit_enforced']:
                report.append("• Enforce pre-commit hooks in CI")
            if not results['test_quality']['fixtures_defined']:
                report.append("• Add test fixtures and factories")
        
        return "\n".join(report)


def main():
    """Run testing validation"""
    validator = TestingValidator()
    results = validator.validate_all()
    
    report = validator.generate_report(results)
    print(report)
    
    # Exit with error code if testing score is low
    if results['overall']['testing_score'] < 80:
        logger.error(f"Testing validation failed with score {results['overall']['testing_score']:.1f}%")
        sys.exit(1)
    else:
        logger.info("Testing validation passed")
        sys.exit(0)


if __name__ == "__main__":
    main()
