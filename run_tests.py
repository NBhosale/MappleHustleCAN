#!/usr/bin/env python3
"""
Comprehensive test runner for MapleHustleCAN
"""
import os
import sys
import subprocess
import argparse
import time
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print(f"{'='*60}")
    
    start_time = time.time()
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    end_time = time.time()
    
    print(f"Duration: {end_time - start_time:.2f} seconds")
    
    if result.returncode != 0:
        print(f"❌ {description} FAILED")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        return False
    else:
        print(f"✅ {description} PASSED")
        if result.stdout:
            print(f"Output: {result.stdout}")
        return True


def setup_test_environment():
    """Setup test environment"""
    print("Setting up test environment...")
    
    # Set environment variables
    os.environ["TESTING"] = "true"
    os.environ["DATABASE_URL"] = "sqlite:///./test.db"
    os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"
    os.environ["ENVIRONMENT"] = "testing"
    os.environ["DEBUG"] = "true"
    os.environ["SECURITY_MONITORING_ENABLED"] = "false"
    os.environ["RATE_LIMIT_ENABLED"] = "false"
    os.environ["CORS_ENABLED"] = "false"
    
    print("✅ Test environment configured")


def run_linting():
    """Run code linting"""
    commands = [
        ("flake8 app/ --count --select=E9,F63,F7,F82 --show-source --statistics", "Flake8 Error Check"),
        ("flake8 app/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics", "Flake8 Style Check"),
        ("mypy app/ --ignore-missing-imports", "MyPy Type Check"),
        ("bandit -r app/ -f json -o bandit-report.json", "Bandit Security Scan"),
        ("safety check --json --output safety-report.json", "Safety Dependency Check")
    ]
    
    all_passed = True
    for command, description in commands:
        if not run_command(command, description):
            all_passed = False
    
    return all_passed


def run_unit_tests():
    """Run unit tests"""
    command = "pytest tests/ -v --cov=app --cov-report=xml --cov-report=html -m 'unit or not (integration or security or load or migration)'"
    return run_command(command, "Unit Tests")


def run_integration_tests():
    """Run integration tests"""
    command = "pytest tests/test_integration.py -v -m integration"
    return run_command(command, "Integration Tests")


def run_security_tests():
    """Run security tests"""
    command = "pytest tests/test_security.py -v -m security"
    return run_command(command, "Security Tests")


def run_migration_tests():
    """Run migration tests"""
    command = "pytest tests/test_migrations.py -v -m migration"
    return run_command(command, "Migration Tests")


def run_load_tests():
    """Run load tests"""
    print("\n" + "="*60)
    print("Running Load Tests")
    print("="*60)
    
    # Check if locust is installed
    try:
        import locust
        print("✅ Locust is available")
    except ImportError:
        print("❌ Locust not installed. Installing...")
        subprocess.run("pip install locust", shell=True)
    
    # Start the application in background
    print("Starting application for load testing...")
    app_process = subprocess.Popen(
        ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for app to start
    time.sleep(5)
    
    # Run load tests
    command = "locust -f tests/load_test.py --host=http://localhost:8000 --users=10 --spawn-rate=2 --run-time=1m --headless --html=load_test_report.html"
    success = run_command(command, "Load Tests")
    
    # Stop the application
    app_process.terminate()
    app_process.wait()
    
    return success


def run_all_tests():
    """Run all tests"""
    print("🚀 Running ALL TESTS for MapleHustleCAN")
    print("="*60)
    
    setup_test_environment()
    
    results = {
        "linting": run_linting(),
        "unit_tests": run_unit_tests(),
        "integration_tests": run_integration_tests(),
        "security_tests": run_security_tests(),
        "migration_tests": run_migration_tests(),
        "load_tests": run_load_tests()
    }
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    all_passed = True
    for test_type, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_type.replace('_', ' ').title()}: {status}")
        if not passed:
            all_passed = False
    
    print("="*60)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("💥 SOME TESTS FAILED!")
        return 1


def run_quick_tests():
    """Run quick tests only"""
    print("⚡ Running QUICK TESTS for MapleHustleCAN")
    print("="*60)
    
    setup_test_environment()
    
    results = {
        "linting": run_linting(),
        "unit_tests": run_unit_tests()
    }
    
    # Print summary
    print("\n" + "="*60)
    print("QUICK TEST SUMMARY")
    print("="*60)
    
    all_passed = True
    for test_type, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_type.replace('_', ' ').title()}: {status}")
        if not passed:
            all_passed = False
    
    print("="*60)
    if all_passed:
        print("🎉 QUICK TESTS PASSED!")
        return 0
    else:
        print("💥 QUICK TESTS FAILED!")
        return 1


def run_ci_tests():
    """Run CI tests (for GitHub Actions)"""
    print("🔄 Running CI TESTS for MapleHustleCAN")
    print("="*60)
    
    setup_test_environment()
    
    # Run database migrations
    print("Running database migrations...")
    migration_success = run_command("alembic upgrade head", "Database Migrations")
    
    if not migration_success:
        print("❌ Database migrations failed!")
        return 1
    
    results = {
        "linting": run_linting(),
        "unit_tests": run_unit_tests(),
        "integration_tests": run_integration_tests(),
        "security_tests": run_security_tests(),
        "migration_tests": run_migration_tests()
    }
    
    # Print summary
    print("\n" + "="*60)
    print("CI TEST SUMMARY")
    print("="*60)
    
    all_passed = True
    for test_type, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_type.replace('_', ' ').title()}: {status}")
        if not passed:
            all_passed = False
    
    print("="*60)
    if all_passed:
        print("🎉 CI TESTS PASSED!")
        return 0
    else:
        print("💥 CI TESTS FAILED!")
        return 1


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="MapleHustleCAN Test Runner")
    parser.add_argument(
        "test_type",
        choices=["all", "quick", "ci", "unit", "integration", "security", "migration", "load", "lint"],
        help="Type of tests to run"
    )
    
    args = parser.parse_args()
    
    if args.test_type == "all":
        return run_all_tests()
    elif args.test_type == "quick":
        return run_quick_tests()
    elif args.test_type == "ci":
        return run_ci_tests()
    elif args.test_type == "unit":
        setup_test_environment()
        return 0 if run_unit_tests() else 1
    elif args.test_type == "integration":
        setup_test_environment()
        return 0 if run_integration_tests() else 1
    elif args.test_type == "security":
        setup_test_environment()
        return 0 if run_security_tests() else 1
    elif args.test_type == "migration":
        setup_test_environment()
        return 0 if run_migration_tests() else 1
    elif args.test_type == "load":
        setup_test_environment()
        return 0 if run_load_tests() else 1
    elif args.test_type == "lint":
        return 0 if run_linting() else 1
    else:
        print(f"Unknown test type: {args.test_type}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
