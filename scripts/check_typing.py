#!/usr/bin/env python3
"""
Type checking script for MapleHustleCAN
Ensures complete typing hints across the codebase
"""

import ast
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TypingChecker:
    """Checks for missing type hints in Python code"""
    
    def __init__(self):
        self.missing_types = []
        self.total_functions = 0
        self.total_classes = 0
    
    def check_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Check a single Python file for missing type hints"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            issues = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    issues.extend(self._check_function(node, file_path))
                elif isinstance(node, ast.AsyncFunctionDef):
                    issues.extend(self._check_async_function(node, file_path))
                elif isinstance(node, ast.ClassDef):
                    issues.extend(self._check_class(node, file_path))
            
            return issues
            
        except Exception as e:
            logger.error(f"Error checking {file_path}: {e}")
            return []
    
    def _check_function(self, node: ast.FunctionDef, file_path: Path) -> List[Dict[str, Any]]:
        """Check function for missing type hints"""
        issues = []
        self.total_functions += 1
        
        # Check return type annotation
        if node.returns is None and not node.name.startswith('_'):
            issues.append({
                'file': str(file_path),
                'line': node.lineno,
                'type': 'function',
                'name': node.name,
                'issue': 'missing_return_type',
                'severity': 'warning'
            })
        
        # Check parameter type annotations
        for arg in node.args.args:
            if arg.annotation is None and not arg.arg.startswith('_'):
                issues.append({
                    'file': str(file_path),
                    'line': node.lineno,
                    'type': 'function',
                    'name': node.name,
                    'issue': f'missing_param_type: {arg.arg}',
                    'severity': 'warning'
                })
        
        # Check default arguments
        for i, default in enumerate(node.args.defaults):
            if default is not None:
                arg_index = len(node.args.args) - len(node.args.defaults) + i
                arg = node.args.args[arg_index]
                if arg.annotation is None:
                    issues.append({
                        'file': str(file_path),
                        'line': node.lineno,
                        'type': 'function',
                        'name': node.name,
                        'issue': f'missing_default_param_type: {arg.arg}',
                        'severity': 'warning'
                    })
        
        return issues
    
    def _check_async_function(self, node: ast.AsyncFunctionDef, file_path: Path) -> List[Dict[str, Any]]:
        """Check async function for missing type hints"""
        issues = []
        self.total_functions += 1
        
        # Check return type annotation
        if node.returns is None and not node.name.startswith('_'):
            issues.append({
                'file': str(file_path),
                'line': node.lineno,
                'type': 'async_function',
                'name': node.name,
                'issue': 'missing_return_type',
                'severity': 'warning'
            })
        
        # Check parameter type annotations
        for arg in node.args.args:
            if arg.annotation is None and not arg.arg.startswith('_'):
                issues.append({
                    'file': str(file_path),
                    'line': node.lineno,
                    'type': 'async_function',
                    'name': node.name,
                    'issue': f'missing_param_type: {arg.arg}',
                    'severity': 'warning'
                })
        
        return issues
    
    def _check_class(self, node: ast.ClassDef, file_path: Path) -> List[Dict[str, Any]]:
        """Check class for missing type hints"""
        issues = []
        self.total_classes += 1
        
        # Check class methods
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                if not item.name.startswith('_') and item.returns is None:
                    issues.append({
                        'file': str(file_path),
                        'line': item.lineno,
                        'type': 'class_method',
                        'name': f"{node.name}.{item.name}",
                        'issue': 'missing_return_type',
                        'severity': 'warning'
                    })
        
        return issues
    
    def check_directory(self, directory: Path) -> List[Dict[str, Any]]:
        """Check all Python files in a directory"""
        all_issues = []
        
        for py_file in directory.rglob("*.py"):
            # Skip __pycache__ and test files for now
            if "__pycache__" in str(py_file) or "test_" in py_file.name:
                continue
            
            issues = self.check_file(py_file)
            all_issues.extend(issues)
        
        return all_issues
    
    def generate_report(self, issues: List[Dict[str, Any]]) -> str:
        """Generate a typing report"""
        if not issues:
            return "✅ All type hints are complete!"
        
        # Group issues by file
        by_file = {}
        for issue in issues:
            file_path = issue['file']
            if file_path not in by_file:
                by_file[file_path] = []
            by_file[file_path].append(issue)
        
        report = []
        report.append("🔍 Type Checking Report")
        report.append("=" * 50)
        report.append(f"Total functions checked: {self.total_functions}")
        report.append(f"Total classes checked: {self.total_classes}")
        report.append(f"Total issues found: {len(issues)}")
        report.append("")
        
        for file_path, file_issues in by_file.items():
            report.append(f"📁 {file_path}")
            report.append("-" * len(file_path))
            
            for issue in file_issues:
                report.append(f"  Line {issue['line']}: {issue['type']} '{issue['name']}' - {issue['issue']}")
            
            report.append("")
        
        return "\n".join(report)


def main():
    """Run type checking"""
    logger.info("🔍 Starting type checking...")
    
    checker = TypingChecker()
    
    # Check app directory
    app_dir = project_root / "app"
    issues = checker.check_directory(app_dir)
    
    # Generate report
    report = checker.generate_report(issues)
    print(report)
    
    # Exit with error code if issues found
    if issues:
        logger.warning(f"Found {len(issues)} typing issues")
        sys.exit(1)
    else:
        logger.info("✅ No typing issues found")
        sys.exit(0)


if __name__ == "__main__":
    main()
