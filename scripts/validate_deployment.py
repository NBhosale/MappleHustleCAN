#!/usr/bin/env python3
"""
Deployment (Docker & Config) Validation Script for MapleHustleCAN
Comprehensive validation of Docker configuration and deployment setup
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


class DeploymentValidator:
    """Comprehensive deployment and Docker validation"""
    
    def __init__(self):
        self.project_root = project_root
        self.docker_compose_dev = project_root / "docker-compose.yml"
        self.docker_compose_prod = project_root / "docker-compose.prod.yml"
        self.dockerfile = project_root / "Dockerfile"
        self.dockerfile_prod = project_root / "Dockerfile.prod"
        self.gitignore = project_root / ".gitignore"
        self.env_example = project_root / ".env.example"
        self.issues = []
        self.passed_checks = []
    
    def check_env_security(self) -> Dict[str, Any]:
        """Check .env file security and .gitignore configuration"""
        logger.info("🔐 Checking .env security...")
        
        checks = {
            'env_not_committed': False,
            'env_in_gitignore': False,
            'env_example_exists': False,
            'gitignore_comprehensive': False
        }
        
        # Check if .env is committed
        try:
            result = os.popen("git ls-files | grep -E '\\.env$'").read().strip()
            if not result:
                checks['env_not_committed'] = True
        except Exception:
            checks['env_not_committed'] = True
        
        # Check .gitignore
        if self.gitignore.exists():
            with open(self.gitignore, 'r') as f:
                gitignore_content = f.read()
                if '.env' in gitignore_content:
                    checks['env_in_gitignore'] = True
                if '.env.local' in gitignore_content and '.env.production.local' in gitignore_content:
                    checks['gitignore_comprehensive'] = True
        
        # Check .env.example
        if self.env_example.exists():
            checks['env_example_exists'] = True
        
        return checks
    
    def check_docker_compose_migrations(self) -> Dict[str, Any]:
        """Check Docker Compose migration startup configuration"""
        logger.info("🗄️ Checking Docker Compose migrations...")
        
        checks = {
            'dev_migrations': False,
            'prod_migrations': False,
            'migration_wait': False,
            'migration_command': False
        }
        
        # Check development docker-compose
        if self.docker_compose_dev.exists():
            with open(self.docker_compose_dev, 'r') as f:
                dev_content = f.read()
                if 'alembic upgrade head' in dev_content:
                    checks['dev_migrations'] = True
                if 'psycopg2.connect' in dev_content or 'wait' in dev_content.lower():
                    checks['migration_wait'] = True
        
        # Check production docker-compose
        if self.docker_compose_prod.exists():
            with open(self.docker_compose_prod, 'r') as f:
                prod_content = f.read()
                if 'alembic upgrade head' in prod_content:
                    checks['prod_migrations'] = True
                if 'gunicorn' in prod_content or 'uvicorn' in prod_content:
                    checks['migration_command'] = True
        
        return checks
    
    def check_dockerfile_multi_stage(self) -> Dict[str, Any]:
        """Check Dockerfile.prod multi-stage build configuration"""
        logger.info("🐳 Checking Dockerfile multi-stage builds...")
        
        checks = {
            'multi_stage_exists': False,
            'builder_stage': False,
            'production_stage': False,
            'security_scanning': False,
            'non_root_user': False,
            'healthcheck_configured': False
        }
        
        if self.dockerfile_prod.exists():
            with open(self.dockerfile_prod, 'r') as f:
                dockerfile_content = f.read()
                
                # Check for multi-stage build
                if 'FROM' in dockerfile_content and 'as' in dockerfile_content:
                    checks['multi_stage_exists'] = True
                
                # Check for builder stage
                if 'as dependencies' in dockerfile_content or 'as build' in dockerfile_content:
                    checks['builder_stage'] = True
                
                # Check for production stage
                if 'as production' in dockerfile_content:
                    checks['production_stage'] = True
                
                # Check for security scanning
                if 'bandit' in dockerfile_content or 'safety' in dockerfile_content:
                    checks['security_scanning'] = True
                
                # Check for non-root user
                if 'appuser' in dockerfile_content and 'USER appuser' in dockerfile_content:
                    checks['non_root_user'] = True
                
                # Check for healthcheck
                if 'HEALTHCHECK' in dockerfile_content:
                    checks['healthcheck_configured'] = True
        
        return checks
    
    def check_healthchecks(self) -> Dict[str, Any]:
        """Check healthcheck configuration in Docker Compose"""
        logger.info("🏥 Checking healthcheck configuration...")
        
        checks = {
            'db_healthcheck': False,
            'redis_healthcheck': False,
            'web_healthcheck': False,
            'nginx_healthcheck': False,
            'healthcheck_intervals': False,
            'healthcheck_timeouts': False
        }
        
        # Check development docker-compose
        if self.docker_compose_dev.exists():
            with open(self.docker_compose_dev, 'r') as f:
                dev_content = f.read()
                if 'pg_isready' in dev_content:
                    checks['db_healthcheck'] = True
                if 'redis-cli ping' in dev_content:
                    checks['redis_healthcheck'] = True
                if 'curl.*health' in dev_content:
                    checks['web_healthcheck'] = True
        
        # Check production docker-compose
        if self.docker_compose_prod.exists():
            with open(self.docker_compose_prod, 'r') as f:
                prod_content = f.read()
                if 'pg_isready' in prod_content:
                    checks['db_healthcheck'] = True
                if 'redis-cli ping' in prod_content:
                    checks['redis_healthcheck'] = True
                if 'curl.*health' in prod_content:
                    checks['web_healthcheck'] = True
                if 'wget.*health' in prod_content:
                    checks['nginx_healthcheck'] = True
                
                # Check for proper intervals and timeouts
                if 'interval: 30s' in prod_content and 'timeout: 10s' in prod_content:
                    checks['healthcheck_intervals'] = True
                    checks['healthcheck_timeouts'] = True
        
        return checks
    
    def check_docker_security(self) -> Dict[str, Any]:
        """Check Docker security configuration"""
        logger.info("🔒 Checking Docker security...")
        
        checks = {
            'non_root_user': False,
            'minimal_base_image': False,
            'no_secrets_in_image': False,
            'security_scanning': False,
            'vulnerability_scanning': False,
            'image_size_optimized': False
        }
        
        if self.dockerfile_prod.exists():
            with open(self.dockerfile_prod, 'r') as f:
                dockerfile_content = f.read()
                
                # Check for non-root user
                if 'USER appuser' in dockerfile_content:
                    checks['non_root_user'] = True
                
                # Check for minimal base image
                if 'python:3.9-slim' in dockerfile_content:
                    checks['minimal_base_image'] = True
                
                # Check for no secrets in image
                if 'COPY .env' not in dockerfile_content and 'COPY *.key' not in dockerfile_content:
                    checks['no_secrets_in_image'] = True
                
                # Check for security scanning
                if 'bandit' in dockerfile_content or 'safety' in dockerfile_content:
                    checks['security_scanning'] = True
                    checks['vulnerability_scanning'] = True
                
                # Check for multi-stage build (indicates size optimization)
                if 'FROM.*as' in dockerfile_content:
                    checks['image_size_optimized'] = True
        
        return checks
    
    def check_production_readiness(self) -> Dict[str, Any]:
        """Check production readiness configuration"""
        logger.info("🚀 Checking production readiness...")
        
        checks = {
            'gunicorn_configured': False,
            'worker_configuration': False,
            'logging_configured': False,
            'monitoring_configured': False,
            'backup_strategy': False,
            'ssl_ready': False
        }
        
        # Check production docker-compose
        if self.docker_compose_prod.exists():
            with open(self.docker_compose_prod, 'r') as f:
                prod_content = f.read()
                
                # Check for Gunicorn
                if 'gunicorn' in prod_content:
                    checks['gunicorn_configured'] = True
                
                # Check for worker configuration
                if '-w 4' in prod_content or 'workers' in prod_content:
                    checks['worker_configuration'] = True
                
                # Check for logging
                if 'logs:' in prod_content or 'logging' in prod_content:
                    checks['logging_configured'] = True
                
                # Check for monitoring
                if 'prometheus' in prod_content or 'grafana' in prod_content:
                    checks['monitoring_configured'] = True
                
                # Check for backup strategy
                if 'backups:' in prod_content or 'backup' in prod_content:
                    checks['backup_strategy'] = True
                
                # Check for SSL readiness
                if '443:443' in prod_content or 'ssl' in prod_content:
                    checks['ssl_ready'] = True
        
        return checks
    
    def validate_all(self) -> Dict[str, Any]:
        """Run all deployment validations"""
        logger.info("🔍 Starting comprehensive deployment validation...")
        
        results = {
            'env_security': self.check_env_security(),
            'docker_compose_migrations': self.check_docker_compose_migrations(),
            'dockerfile_multi_stage': self.check_dockerfile_multi_stage(),
            'healthchecks': self.check_healthchecks(),
            'docker_security': self.check_docker_security(),
            'production_readiness': self.check_production_readiness()
        }
        
        # Calculate overall deployment score
        total_checks = 0
        passed_checks = 0
        
        for category, checks in results.items():
            for check, passed in checks.items():
                total_checks += 1
                if passed:
                    passed_checks += 1
        
        deployment_score = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
        
        results['overall'] = {
            'total_checks': total_checks,
            'passed_checks': passed_checks,
            'deployment_score': deployment_score,
            'status': 'PASS' if deployment_score >= 80 else 'FAIL'
        }
        
        return results
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate deployment validation report"""
        report = []
        report.append("🐳 Deployment (Docker & Config) Validation Report")
        report.append("=" * 60)
        report.append("")
        
        # Overall status
        overall = results['overall']
        report.append(f"📊 Overall Deployment Score: {overall['deployment_score']:.1f}%")
        report.append(f"✅ Passed Checks: {overall['passed_checks']}/{overall['total_checks']}")
        report.append(f"🎯 Status: {overall['status']}")
        report.append("")
        
        # Category breakdown
        categories = {
            'env_security': '🔐 Environment Security',
            'docker_compose_migrations': '🗄️ Docker Compose Migrations',
            'dockerfile_multi_stage': '🐳 Dockerfile Multi-stage',
            'healthchecks': '🏥 Healthchecks',
            'docker_security': '🔒 Docker Security',
            'production_readiness': '🚀 Production Readiness'
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
        if overall['deployment_score'] < 80:
            report.append("⚠️ Deployment Recommendations:")
            report.append("-" * 35)
            
            if not results['env_security']['env_not_committed']:
                report.append("• Ensure .env file is not committed to git")
            if not results['docker_compose_migrations']['prod_migrations']:
                report.append("• Add migration startup to production docker-compose")
            if not results['dockerfile_multi_stage']['multi_stage_exists']:
                report.append("• Implement multi-stage Docker builds")
            if not results['healthchecks']['web_healthcheck']:
                report.append("• Add healthchecks for all services")
            if not results['docker_security']['non_root_user']:
                report.append("• Use non-root user in Docker containers")
            if not results['production_readiness']['gunicorn_configured']:
                report.append("• Configure Gunicorn for production")
        
        return "\n".join(report)


def main():
    """Run deployment validation"""
    validator = DeploymentValidator()
    results = validator.validate_all()
    
    report = validator.generate_report(results)
    print(report)
    
    # Exit with error code if deployment score is low
    if results['overall']['deployment_score'] < 80:
        logger.error(f"Deployment validation failed with score {results['overall']['deployment_score']:.1f}%")
        sys.exit(1)
    else:
        logger.info("Deployment validation passed")
        sys.exit(0)


if __name__ == "__main__":
    main()
