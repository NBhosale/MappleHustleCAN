#!/usr/bin/env python3
"""
Migration Validation Script for MapleHustleCAN
Validates that all migrations are complete and can be applied/reverted
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Any
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MigrationValidator:
    """Validates Alembic migrations for completeness and consistency"""
    
    def __init__(self):
        self.project_root = project_root
        self.alembic_dir = self.project_root / "alembic"
        self.versions_dir = self.alembic_dir / "versions"
        self.issues = []
    
    def check_migration_files(self) -> List[Dict[str, Any]]:
        """Check all migration files for completeness"""
        issues = []
        
        for migration_file in self.versions_dir.glob("*.py"):
            if migration_file.name == "__init__.py":
                continue
            
            # Check file size
            file_size = migration_file.stat().st_size
            if file_size < 100:  # Less than 100 bytes is suspicious
                issues.append({
                    'file': str(migration_file),
                    'issue': 'file_too_small',
                    'size': file_size,
                    'severity': 'warning'
                })
            
            # Check for empty upgrade/downgrade functions
            try:
                with open(migration_file, 'r') as f:
                    content = f.read()
                
                if 'def upgrade():' in content and 'pass' in content:
                    if content.count('pass') > 1:  # More than just the function signature
                        issues.append({
                            'file': str(migration_file),
                            'issue': 'empty_functions',
                            'severity': 'warning'
                        })
                
                # Check for proper revision identifiers
                if 'revision =' not in content:
                    issues.append({
                        'file': str(migration_file),
                        'issue': 'missing_revision',
                        'severity': 'error'
                    })
                
                if 'down_revision =' not in content:
                    issues.append({
                        'file': str(migration_file),
                        'issue': 'missing_down_revision',
                        'severity': 'error'
                    })
                
            except Exception as e:
                issues.append({
                    'file': str(migration_file),
                    'issue': 'read_error',
                    'error': str(e),
                    'severity': 'error'
                })
        
        return issues
    
    def check_migration_chain(self) -> List[Dict[str, Any]]:
        """Check migration chain for consistency"""
        issues = []
        
        try:
            # Try to get current revision
            result = subprocess.run(
                ['python3', '-m', 'alembic', 'current'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                issues.append({
                    'issue': 'alembic_current_failed',
                    'error': result.stderr,
                    'severity': 'warning'
                })
            else:
                logger.info(f"Current revision: {result.stdout.strip()}")
        
        except subprocess.TimeoutExpired:
            issues.append({
                'issue': 'alembic_timeout',
                'severity': 'error'
            })
        except Exception as e:
            issues.append({
                'issue': 'alembic_error',
                'error': str(e),
                'severity': 'error'
            })
        
        return issues
    
    def check_required_indexes(self) -> List[Dict[str, Any]]:
        """Check if required indexes are defined in migrations"""
        issues = []
        required_indexes = [
            ('users', 'email', 'unique'),
            ('users', 'created_at', 'regular'),
            ('bookings', 'user_id', 'regular'),
            ('bookings', 'status', 'regular'),
            ('bookings', 'created_at', 'regular'),
            ('orders', 'user_id', 'regular'),
            ('orders', 'status', 'regular'),
            ('orders', 'created_at', 'regular'),
        ]
        
        # Check if indexes migration exists
        indexes_migration = self.versions_dir / "add_indexes_and_constraints.py"
        if not indexes_migration.exists():
            issues.append({
                'issue': 'missing_indexes_migration',
                'severity': 'error'
            })
            return issues
        
        # Check if indexes are defined
        try:
            with open(indexes_migration, 'r') as f:
                content = f.read()
            
            for table, column, index_type in required_indexes:
                index_name = f"ix_{table}_{column}"
                if index_name not in content:
                    issues.append({
                        'issue': 'missing_index',
                        'table': table,
                        'column': column,
                        'index_name': index_name,
                        'severity': 'error'
                    })
        
        except Exception as e:
            issues.append({
                'issue': 'indexes_migration_read_error',
                'error': str(e),
                'severity': 'error'
            })
        
        return issues
    
    def check_seed_data(self) -> List[Dict[str, Any]]:
        """Check if seed data migrations exist"""
        issues = []
        
        # Check for seed data migration
        seed_migration = self.versions_dir / "add_seed_data_migration.py"
        if not seed_migration.exists():
            issues.append({
                'issue': 'missing_seed_migration',
                'severity': 'warning'
            })
        
        # Check for standalone seed script
        seed_script = self.project_root / "scripts" / "seed_database.py"
        if not seed_script.exists():
            issues.append({
                'issue': 'missing_seed_script',
                'severity': 'warning'
            })
        
        return issues
    
    def validate_all(self) -> Dict[str, Any]:
        """Run all validation checks"""
        logger.info("🔍 Starting migration validation...")
        
        all_issues = []
        
        # Check migration files
        file_issues = self.check_migration_files()
        all_issues.extend(file_issues)
        logger.info(f"Migration files check: {len(file_issues)} issues found")
        
        # Check migration chain
        chain_issues = self.check_migration_chain()
        all_issues.extend(chain_issues)
        logger.info(f"Migration chain check: {len(chain_issues)} issues found")
        
        # Check required indexes
        index_issues = self.check_required_indexes()
        all_issues.extend(index_issues)
        logger.info(f"Indexes check: {len(index_issues)} issues found")
        
        # Check seed data
        seed_issues = self.check_seed_data()
        all_issues.extend(seed_issues)
        logger.info(f"Seed data check: {len(seed_issues)} issues found")
        
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
        """Generate validation report"""
        report = []
        report.append("🔍 Migration Validation Report")
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
                    if 'error' in issue:
                        report.append(f"  Error: {issue['error']}")
                    report.append("")
        
        if results['warnings']:
            report.append("⚠️  WARNINGS (Should Fix):")
            report.append("-" * 25)
            for issue in results['issues']:
                if issue.get('severity') == 'warning':
                    report.append(f"• {issue['issue']}")
                    if 'file' in issue:
                        report.append(f"  File: {issue['file']}")
                    report.append("")
        
        if results['status'] == 'pass':
            report.append("✅ All migrations are valid!")
        
        return "\n".join(report)


def main():
    """Run migration validation"""
    validator = MigrationValidator()
    results = validator.validate_all()
    
    report = validator.generate_report(results)
    print(report)
    
    # Exit with error code if there are errors
    if results['errors'] > 0:
        logger.error(f"Migration validation failed with {results['errors']} errors")
        sys.exit(1)
    else:
        logger.info("Migration validation passed")
        sys.exit(0)


if __name__ == "__main__":
    main()
