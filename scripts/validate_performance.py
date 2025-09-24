#!/usr/bin/env python3
"""
Performance & Scalability Validation Script for MapleHustleCAN
Comprehensive validation of caching, background tasks, query optimization, and database pooling
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Any
import logging
import ast

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PerformanceValidator:
    """Comprehensive performance and scalability validation"""
    
    def __init__(self):
        self.project_root = project_root
        self.app_dir = project_root / "app"
        self.tasks_dir = self.app_dir / "tasks"
        self.core_dir = self.app_dir / "core"
        self.repositories_dir = self.app_dir / "repositories"
        self.db_dir = self.app_dir / "db"
        self.issues = []
        self.passed_checks = []
    
    def check_redis_caching(self) -> Dict[str, Any]:
        """Check Redis caching implementation"""
        logger.info("🔍 Checking Redis caching...")
        
        checks = {
            'cache_manager_exists': False,
            'redis_connection_pool': False,
            'cache_decorators': False,
            'cache_utilities': False,
            'redis_config': False,
            'cache_invalidation': False
        }
        
        # Check cache.py
        cache_file = self.core_dir / "cache.py"
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                cache_content = f.read()
                
                if 'class CacheManager' in cache_content:
                    checks['cache_manager_exists'] = True
                
                if 'ConnectionPool' in cache_content and 'max_connections' in cache_content:
                    checks['redis_connection_pool'] = True
                
                if '@cached' in cache_content and 'def cached(' in cache_content:
                    checks['cache_decorators'] = True
                
                if 'cache_user' in cache_content and 'cache_service' in cache_content:
                    checks['cache_utilities'] = True
                
                if 'invalidate_cache' in cache_content:
                    checks['cache_invalidation'] = True
        
        # Check Redis configuration
        config_file = self.core_dir / "config.py"
        if config_file.exists():
            with open(config_file, 'r') as f:
                config_content = f.read()
                if 'REDIS_URL' in config_content:
                    checks['redis_config'] = True
        
        return checks
    
    def check_celery_background_tasks(self) -> Dict[str, Any]:
        """Check Celery background task implementation"""
        logger.info("🔍 Checking Celery background tasks...")
        
        checks = {
            'celery_app_exists': False,
            'task_files_exist': False,
            'email_tasks': False,
            'sms_tasks': False,
            'notification_tasks': False,
            'file_tasks': False,
            'cleanup_tasks': False,
            'task_routing': False,
            'beat_schedule': False,
            'retry_config': False
        }
        
        # Check celery_app.py
        celery_file = self.core_dir / "celery_app.py"
        if celery_file.exists():
            with open(celery_file, 'r') as f:
                celery_content = f.read()
                
                if 'celery_app = Celery(' in celery_content:
                    checks['celery_app_exists'] = True
                
                if 'task_routes' in celery_content:
                    checks['task_routing'] = True
                
                if 'beat_schedule' in celery_content:
                    checks['beat_schedule'] = True
                
                if 'task_default_retry_delay' in celery_content and 'task_max_retries' in celery_content:
                    checks['retry_config'] = True
        
        # Check task files
        task_files = [
            'email_tasks.py',
            'sms_tasks.py', 
            'notification_tasks.py',
            'file_tasks.py',
            'cleanup_tasks.py'
        ]
        
        existing_tasks = 0
        for task_file in task_files:
            task_path = self.tasks_dir / task_file
            if task_path.exists():
                existing_tasks += 1
                
                # Check specific task types
                if task_file == 'email_tasks.py':
                    checks['email_tasks'] = True
                elif task_file == 'sms_tasks.py':
                    checks['sms_tasks'] = True
                elif task_file == 'notification_tasks.py':
                    checks['notification_tasks'] = True
                elif task_file == 'file_tasks.py':
                    checks['file_tasks'] = True
                elif task_file == 'cleanup_tasks.py':
                    checks['cleanup_tasks'] = True
        
        if existing_tasks >= 3:
            checks['task_files_exist'] = True
        
        return checks
    
    def check_n1_query_optimization(self) -> Dict[str, Any]:
        """Check N+1 query optimization"""
        logger.info("🔍 Checking N+1 query optimization...")
        
        checks = {
            'optimized_queries_exists': False,
            'selectinload_usage': False,
            'joinedload_usage': False,
            'eager_loading_patterns': False,
            'query_optimization_classes': False,
            'relationship_loading': False
        }
        
        # Check optimized_queries.py
        optimized_file = self.repositories_dir / "optimized_queries.py"
        if optimized_file.exists():
            with open(optimized_file, 'r') as f:
                optimized_content = f.read()
                
                if 'optimized_queries.py' in optimized_content:
                    checks['optimized_queries_exists'] = True
                
                if 'selectinload' in optimized_content:
                    checks['selectinload_usage'] = True
                
                if 'joinedload' in optimized_content:
                    checks['joinedload_usage'] = True
                
                if 'class Optimized' in optimized_content:
                    checks['query_optimization_classes'] = True
                
                if 'eager loading' in optimized_content.lower():
                    checks['eager_loading_patterns'] = True
                
                if 'User.services' in optimized_content or 'User.bookings' in optimized_content:
                    checks['relationship_loading'] = True
        
        return checks
    
    def check_database_pooling(self) -> Dict[str, Any]:
        """Check database connection pooling"""
        logger.info("🔍 Checking database pooling...")
        
        checks = {
            'pooling_config_exists': False,
            'pool_size_configured': False,
            'max_overflow_configured': False,
            'pool_pre_ping': False,
            'pool_recycle': False,
            'connection_monitoring': False,
            'health_checks': False,
            'transaction_management': False
        }
        
        # Check session.py
        session_file = self.db_dir / "session.py"
        if session_file.exists():
            with open(session_file, 'r') as f:
                session_content = f.read()
                
                if 'pool_size' in session_content and 'max_overflow' in session_content:
                    checks['pooling_config_exists'] = True
                    checks['pool_size_configured'] = True
                    checks['max_overflow_configured'] = True
                
                if 'pool_pre_ping' in session_content:
                    checks['pool_pre_ping'] = True
                
                if 'pool_recycle' in session_content:
                    checks['pool_recycle'] = True
                
                if 'ConnectionMonitor' in session_content:
                    checks['connection_monitoring'] = True
                
                if 'health_check' in session_content:
                    checks['health_checks'] = True
                
                if 'TransactionManager' in session_content:
                    checks['transaction_management'] = True
        
        return checks
    
    def check_caching_integration(self) -> Dict[str, Any]:
        """Check caching integration in routers and services"""
        logger.info("🔍 Checking caching integration...")
        
        checks = {
            'cached_services_router': False,
            'cache_usage_in_routers': False,
            'cache_usage_in_services': False,
            'cache_key_generation': False,
            'cache_invalidation_patterns': False
        }
        
        # Check for cached services router
        cached_services_file = self.app_dir / "routers" / "cached_services.py"
        if cached_services_file.exists():
            checks['cached_services_router'] = True
        
        # Check routers for cache usage
        routers_dir = self.app_dir / "routers"
        cache_usage_found = False
        for router_file in routers_dir.glob("*.py"):
            if router_file.name != "__init__.py":
                with open(router_file, 'r') as f:
                    content = f.read()
                    if 'cache' in content.lower() or 'redis' in content.lower():
                        cache_usage_found = True
                        break
        
        if cache_usage_found:
            checks['cache_usage_in_routers'] = True
        
        # Check services for cache usage
        services_dir = self.app_dir / "services"
        if services_dir.exists():
            for service_file in services_dir.glob("*.py"):
                if service_file.name != "__init__.py":
                    with open(service_file, 'r') as f:
                        content = f.read()
                        if 'cache' in content.lower() or 'redis' in content.lower():
                            checks['cache_usage_in_services'] = True
                            break
        
        # Check cache key generation
        cache_file = self.core_dir / "cache.py"
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                content = f.read()
                if 'def cache_key(' in content:
                    checks['cache_key_generation'] = True
                
                if 'invalidate_user_cache' in content or 'invalidate_service_cache' in content:
                    checks['cache_invalidation_patterns'] = True
        
        return checks
    
    def check_background_task_integration(self) -> Dict[str, Any]:
        """Check background task integration in routers"""
        logger.info("🔍 Checking background task integration...")
        
        checks = {
            'email_tasks_in_routers': False,
            'sms_tasks_in_routers': False,
            'notification_tasks_in_routers': False,
            'file_tasks_in_routers': False,
            'async_task_calls': False,
            'task_error_handling': False
        }
        
        # Check routers for background task usage
        routers_dir = self.app_dir / "routers"
        for router_file in routers_dir.glob("*.py"):
            if router_file.name != "__init__.py":
                with open(router_file, 'r') as f:
                    content = f.read()
                    
                    if 'email_tasks' in content or 'send_email' in content:
                        checks['email_tasks_in_routers'] = True
                    
                    if 'sms_tasks' in content or 'send_sms' in content:
                        checks['sms_tasks_in_routers'] = True
                    
                    if 'notification_tasks' in content or 'create_notification' in content:
                        checks['notification_tasks_in_routers'] = True
                    
                    if 'file_tasks' in content or 'process_file' in content:
                        checks['file_tasks_in_routers'] = True
                    
                    if '.delay(' in content or '.apply_async(' in content:
                        checks['async_task_calls'] = True
                    
                    if 'try:' in content and 'except' in content and 'task' in content.lower():
                        checks['task_error_handling'] = True
        
        return checks
    
    def check_performance_monitoring(self) -> Dict[str, Any]:
        """Check performance monitoring implementation"""
        logger.info("🔍 Checking performance monitoring...")
        
        checks = {
            'query_monitoring': False,
            'connection_monitoring': False,
            'cache_monitoring': False,
            'task_monitoring': False,
            'performance_metrics': False,
            'slow_query_detection': False
        }
        
        # Check session.py for query monitoring
        session_file = self.db_dir / "session.py"
        if session_file.exists():
            with open(session_file, 'r') as f:
                content = f.read()
                if 'ConnectionMonitor' in content and 'log_query_time' in content:
                    checks['query_monitoring'] = True
                    checks['connection_monitoring'] = True
                
                if 'slow_query_threshold' in content:
                    checks['slow_query_detection'] = True
        
        # Check cache.py for cache monitoring
        cache_file = self.core_dir / "cache.py"
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                content = f.read()
                if 'info()' in content and 'redis' in content.lower():
                    checks['cache_monitoring'] = True
        
        # Check for performance metrics
        if 'performance' in str(self.app_dir) or 'metrics' in str(self.app_dir):
            checks['performance_metrics'] = True
        
        # Check Celery for task monitoring
        celery_file = self.core_dir / "celery_app.py"
        if celery_file.exists():
            with open(celery_file, 'r') as f:
                content = f.read()
                if 'worker_send_task_events' in content and 'task_send_sent_event' in content:
                    checks['task_monitoring'] = True
        
        return checks
    
    def validate_all(self) -> Dict[str, Any]:
        """Run all performance validations"""
        logger.info("🔍 Starting comprehensive performance validation...")
        
        results = {
            'redis_caching': self.check_redis_caching(),
            'celery_background_tasks': self.check_celery_background_tasks(),
            'n1_query_optimization': self.check_n1_query_optimization(),
            'database_pooling': self.check_database_pooling(),
            'caching_integration': self.check_caching_integration(),
            'background_task_integration': self.check_background_task_integration(),
            'performance_monitoring': self.check_performance_monitoring()
        }
        
        # Calculate overall performance score
        total_checks = 0
        passed_checks = 0
        
        for category, checks in results.items():
            for check, passed in checks.items():
                total_checks += 1
                if passed:
                    passed_checks += 1
        
        performance_score = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
        
        results['overall'] = {
            'total_checks': total_checks,
            'passed_checks': passed_checks,
            'performance_score': performance_score,
            'status': 'PASS' if performance_score >= 80 else 'FAIL'
        }
        
        return results
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate performance validation report"""
        report = []
        report.append("⚡ Performance & Scalability Validation Report")
        report.append("=" * 60)
        report.append("")
        
        # Overall status
        overall = results['overall']
        report.append(f"📊 Overall Performance Score: {overall['performance_score']:.1f}%")
        report.append(f"✅ Passed Checks: {overall['passed_checks']}/{overall['total_checks']}")
        report.append(f"🎯 Status: {overall['status']}")
        report.append("")
        
        # Category breakdown
        categories = {
            'redis_caching': '🔴 Redis Caching',
            'celery_background_tasks': '🔄 Background Tasks',
            'n1_query_optimization': '🔍 Query Optimization',
            'database_pooling': '🗄️ Database Pooling',
            'caching_integration': '🔗 Caching Integration',
            'background_task_integration': '🔗 Task Integration',
            'performance_monitoring': '📊 Performance Monitoring'
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
        if overall['performance_score'] < 80:
            report.append("⚠️ Performance Recommendations:")
            report.append("-" * 35)
            
            if not results['redis_caching']['cache_manager_exists']:
                report.append("• Implement Redis caching layer")
            if not results['celery_background_tasks']['celery_app_exists']:
                report.append("• Set up Celery for background tasks")
            if not results['n1_query_optimization']['selectinload_usage']:
                report.append("• Implement N+1 query optimization")
            if not results['database_pooling']['pool_size_configured']:
                report.append("• Configure database connection pooling")
            if not results['caching_integration']['cache_usage_in_routers']:
                report.append("• Integrate caching in routers and services")
            if not results['background_task_integration']['async_task_calls']:
                report.append("• Move blocking operations to background tasks")
        
        return "\n".join(report)


def main():
    """Run performance validation"""
    validator = PerformanceValidator()
    results = validator.validate_all()
    
    report = validator.generate_report(results)
    print(report)
    
    # Exit with error code if performance score is low
    if results['overall']['performance_score'] < 80:
        logger.error(f"Performance validation failed with score {results['overall']['performance_score']:.1f}%")
        sys.exit(1)
    else:
        logger.info("Performance validation passed")
        sys.exit(0)


if __name__ == "__main__":
    main()
