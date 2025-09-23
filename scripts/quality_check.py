#!/usr/bin/env python3
"""
Comprehensive code quality check script for MapleHustleCAN
"""
import os
import sys
import subprocess
import argparse
import json
from pathlib import Path
from typing import Dict, Any, List


class QualityChecker:
    """Code quality checker with multiple tools"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.results = {}
    
    def run_command(self, command: List[str], description: str) -> Dict[str, Any]:
        """Run a command and return results"""
        print(f"\n{'='*60}")
        print(f"Running: {description}")
        print(f"Command: {' '.join(command)}")
        print(f"{'='*60}")
        
        try:
            result = subprocess.run(
                command,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Command timed out after 5 minutes",
                "returncode": -1
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1
            }
    
    def check_black(self) -> Dict[str, Any]:
        """Check code formatting with Black"""
        result = self.run_command(
            ["black", "--check", "--diff", "app/"],
            "Black Code Formatting Check"
        )
        
        if not result["success"]:
            print("❌ Code formatting issues found:")
            print(result["stdout"])
        else:
            print("✅ Code formatting is correct")
        
        return result
    
    def check_isort(self) -> Dict[str, Any]:
        """Check import sorting with isort"""
        result = self.run_command(
            ["isort", "--check-only", "--diff", "app/"],
            "Import Sorting Check"
        )
        
        if not result["success"]:
            print("❌ Import sorting issues found:")
            print(result["stdout"])
        else:
            print("✅ Import sorting is correct")
        
        return result
    
    def check_flake8(self) -> Dict[str, Any]:
        """Check code style with flake8"""
        result = self.run_command(
            ["flake8", "app/", "--max-line-length=88", "--extend-ignore=E203,W503"],
            "Flake8 Style Check"
        )
        
        if not result["success"]:
            print("❌ Style issues found:")
            print(result["stdout"])
        else:
            print("✅ No style issues found")
        
        return result
    
    def check_mypy(self) -> Dict[str, Any]:
        """Check type hints with mypy"""
        result = self.run_command(
            ["mypy", "app/", "--ignore-missing-imports"],
            "MyPy Type Check"
        )
        
        if not result["success"]:
            print("❌ Type checking issues found:")
            print(result["stdout"])
        else:
            print("✅ Type checking passed")
        
        return result
    
    def check_bandit(self) -> Dict[str, Any]:
        """Check security issues with bandit"""
        result = self.run_command(
            ["bandit", "-r", "app/", "-f", "json", "-o", "bandit-report.json"],
            "Bandit Security Check"
        )
        
        # Bandit returns non-zero for security issues, but we want to see them
        if result["returncode"] != 0:
            print("⚠️  Security issues found (see bandit-report.json)")
        else:
            print("✅ No security issues found")
        
        return result
    
    def check_safety(self) -> Dict[str, Any]:
        """Check dependencies with safety"""
        result = self.run_command(
            ["safety", "check", "--json", "--output", "safety-report.json"],
            "Safety Dependency Check"
        )
        
        if not result["success"]:
            print("⚠️  Dependency vulnerabilities found (see safety-report.json)")
        else:
            print("✅ No dependency vulnerabilities found")
        
        return result
    
    def check_pylint(self) -> Dict[str, Any]:
        """Check code quality with pylint"""
        result = self.run_command(
            ["pylint", "app/", "--disable=C0114,C0115,C0116,R0903,R0913,W0613,C0103"],
            "Pylint Code Quality Check"
        )
        
        if not result["success"]:
            print("❌ Code quality issues found:")
            print(result["stdout"])
        else:
            print("✅ Code quality check passed")
        
        return result
    
    def check_docstrings(self) -> Dict[str, Any]:
        """Check for missing docstrings"""
        missing_docstrings = []
        
        for py_file in self.project_root.glob("app/**/*.py"):
            if "test" in str(py_file) or "migration" in str(py_file):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                lines = content.split('\n')
                in_class = False
                in_function = False
                class_name = ""
                function_name = ""
                
                for i, line in enumerate(lines):
                    stripped = line.strip()
                    
                    # Check for class definition
                    if stripped.startswith('class '):
                        in_class = True
                        class_name = stripped.split('(')[0].split('class ')[1]
                        in_function = False
                        
                        # Check if class has docstring
                        if i + 1 < len(lines) and not lines[i + 1].strip().startswith('"""'):
                            missing_docstrings.append(f"{py_file}:{i+1} - Class '{class_name}' missing docstring")
                    
                    # Check for function definition
                    elif stripped.startswith('def ') and not stripped.startswith('def _'):
                        in_function = True
                        function_name = stripped.split('(')[0].split('def ')[1]
                        
                        # Check if function has docstring
                        if i + 1 < len(lines) and not lines[i + 1].strip().startswith('"""'):
                            missing_docstrings.append(f"{py_file}:{i+1} - Function '{function_name}' missing docstring")
                    
                    # Reset flags
                    elif stripped and not stripped.startswith(' ') and not stripped.startswith('#'):
                        in_class = False
                        in_function = False
            
            except Exception as e:
                print(f"Error checking {py_file}: {e}")
        
        if missing_docstrings:
            print("❌ Missing docstrings found:")
            for docstring in missing_docstrings[:10]:  # Show first 10
                print(f"  {docstring}")
            if len(missing_docstrings) > 10:
                print(f"  ... and {len(missing_docstrings) - 10} more")
        else:
            print("✅ All functions and classes have docstrings")
        
        return {
            "success": len(missing_docstrings) == 0,
            "missing_docstrings": missing_docstrings,
            "count": len(missing_docstrings)
        }
    
    def check_hardcoded_values(self) -> Dict[str, Any]:
        """Check for hardcoded values that should be in config"""
        hardcoded_values = []
        
        # Common hardcoded values to check for
        patterns = [
            ("localhost", "Use settings.ALLOWED_HOSTS"),
            ("127.0.0.1", "Use settings.ALLOWED_HOSTS"),
            ("postgresql://", "Use settings.DATABASE_URL"),
            ("redis://", "Use settings.REDIS_URL"),
            ("smtp.gmail.com", "Use settings.SMTP_HOST"),
            ("jwt", "Use settings.JWT_SECRET_KEY"),
            ("secret", "Use settings for secrets"),
            ("password", "Use settings for passwords"),
            ("token", "Use settings for tokens"),
            ("api_key", "Use settings for API keys"),
        ]
        
        for py_file in self.project_root.glob("app/**/*.py"):
            if "test" in str(py_file) or "migration" in str(py_file) or "config.py" in str(py_file):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for i, line in enumerate(content.split('\n')):
                    for pattern, suggestion in patterns:
                        if pattern in line.lower() and not line.strip().startswith('#'):
                            hardcoded_values.append(f"{py_file}:{i+1} - Found '{pattern}': {suggestion}")
            
            except Exception as e:
                print(f"Error checking {py_file}: {e}")
        
        if hardcoded_values:
            print("⚠️  Potential hardcoded values found:")
            for value in hardcoded_values[:10]:  # Show first 10
                print(f"  {value}")
            if len(hardcoded_values) > 10:
                print(f"  ... and {len(hardcoded_values) - 10} more")
        else:
            print("✅ No hardcoded values found")
        
        return {
            "success": len(hardcoded_values) == 0,
            "hardcoded_values": hardcoded_values,
            "count": len(hardcoded_values)
        }
    
    def run_all_checks(self) -> Dict[str, Any]:
        """Run all quality checks"""
        print("🔍 Running comprehensive code quality checks...")
        
        checks = {
            "black": self.check_black(),
            "isort": self.check_isort(),
            "flake8": self.check_flake8(),
            "mypy": self.check_mypy(),
            "bandit": self.check_bandit(),
            "safety": self.check_safety(),
            "pylint": self.check_pylint(),
            "docstrings": self.check_docstrings(),
            "hardcoded_values": self.check_hardcoded_values()
        }
        
        self.results = checks
        return checks
    
    def generate_report(self) -> str:
        """Generate quality report"""
        total_checks = len(self.results)
        passed_checks = sum(1 for result in self.results.values() if result.get("success", False))
        failed_checks = total_checks - passed_checks
        
        report = f"""
{'='*60}
CODE QUALITY REPORT
{'='*60}

Total Checks: {total_checks}
Passed: {passed_checks}
Failed: {failed_checks}
Success Rate: {(passed_checks/total_checks)*100:.1f}%

{'='*60}
DETAILED RESULTS
{'='*60}
"""
        
        for check_name, result in self.results.items():
            status = "✅ PASS" if result.get("success", False) else "❌ FAIL"
            report += f"{check_name.upper()}: {status}\n"
            
            if not result.get("success", False) and result.get("count"):
                report += f"  Issues found: {result['count']}\n"
        
        return report


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="MapleHustleCAN Code Quality Checker")
    parser.add_argument(
        "check_type",
        choices=["all", "format", "style", "types", "security", "deps", "quality", "docs", "hardcoded"],
        help="Type of quality check to run"
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Project root directory"
    )
    parser.add_argument(
        "--output",
        help="Output file for report"
    )
    
    args = parser.parse_args()
    
    checker = QualityChecker(args.project_root)
    
    if args.check_type == "all":
        results = checker.run_all_checks()
    elif args.check_type == "format":
        results = {"black": checker.check_black(), "isort": checker.check_isort()}
    elif args.check_type == "style":
        results = {"flake8": checker.check_flake8(), "pylint": checker.check_pylint()}
    elif args.check_type == "types":
        results = {"mypy": checker.check_mypy()}
    elif args.check_type == "security":
        results = {"bandit": checker.check_bandit(), "safety": checker.check_safety()}
    elif args.check_type == "deps":
        results = {"safety": checker.check_safety()}
    elif args.check_type == "quality":
        results = {"pylint": checker.check_pylint(), "docstrings": checker.check_docstrings()}
    elif args.check_type == "docs":
        results = {"docstrings": checker.check_docstrings()}
    elif args.check_type == "hardcoded":
        results = {"hardcoded_values": checker.check_hardcoded_values()}
    
    # Generate and display report
    report = checker.generate_report()
    print(report)
    
    # Save report if requested
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"Report saved to {args.output}")
    
    # Exit with error code if any checks failed
    failed_checks = sum(1 for result in results.values() if not result.get("success", False))
    if failed_checks > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
