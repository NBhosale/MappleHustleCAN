"""
Cleanup background tasks for MapleHustleCAN
"""
import logging
import os
import shutil
from datetime import datetime, timedelta
from typing import List, Dict, Any
from celery import current_task
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.celery_app import celery_app
from app.core.config import settings
from app.db.session import get_session_factory

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def cleanup_expired_tokens(self):
    """Clean up expired refresh tokens"""
    try:
        session_factory = get_session_factory()
        with session_factory() as db:
            # Delete expired refresh tokens
            result = db.execute(text("""
                DELETE FROM refresh_tokens 
                WHERE expires_at < NOW()
            """))
            
            deleted_count = result.rowcount
            db.commit()
            
            logger.info(f"Cleaned up {deleted_count} expired refresh tokens")
            return {"status": "success", "deleted_tokens": deleted_count}
            
    except Exception as exc:
        logger.error(f"Failed to cleanup expired tokens: {exc}")
        raise self.retry(exc=exc, countdown=300)  # Retry in 5 minutes


@celery_app.task(bind=True)
def cleanup_old_sessions(self):
    """Clean up old user sessions"""
    try:
        session_factory = get_session_factory()
        with session_factory() as db:
            # Delete sessions older than 30 days
            result = db.execute(text("""
                DELETE FROM sessions 
                WHERE last_activity < NOW() - INTERVAL '30 days'
            """))
            
            deleted_count = result.rowcount
            db.commit()
            
            logger.info(f"Cleaned up {deleted_count} old sessions")
            return {"status": "success", "deleted_sessions": deleted_count}
            
    except Exception as exc:
        logger.error(f"Failed to cleanup old sessions: {exc}")
        raise self.retry(exc=exc, countdown=300)


@celery_app.task(bind=True)
def cleanup_temp_files(self):
    """Clean up temporary files"""
    try:
        temp_dirs = [
            "/tmp/maplehustlecan",
            "uploads/temp",
            "logs/temp"
        ]
        
        total_deleted = 0
        total_size = 0
        
        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            # Delete files older than 24 hours
                            if os.path.getmtime(file_path) < (datetime.now().timestamp() - 86400):
                                file_size = os.path.getsize(file_path)
                                os.remove(file_path)
                                total_deleted += 1
                                total_size += file_size
                        except Exception as e:
                            logger.warning(f"Failed to delete temp file {file_path}: {e}")
        
        logger.info(f"Cleaned up {total_deleted} temp files ({total_size / 1024 / 1024:.2f} MB)")
        return {
            "status": "success", 
            "deleted_files": total_deleted, 
            "freed_space_mb": round(total_size / 1024 / 1024, 2)
        }
        
    except Exception as exc:
        logger.error(f"Failed to cleanup temp files: {exc}")
        raise self.retry(exc=exc, countdown=300)


@celery_app.task(bind=True)
def cleanup_old_logs(self):
    """Clean up old log files"""
    try:
        log_dirs = ["logs", "app/logs"]
        total_deleted = 0
        total_size = 0
        
        for log_dir in log_dirs:
            if os.path.exists(log_dir):
                for file in os.listdir(log_dir):
                    if file.endswith('.log'):
                        file_path = os.path.join(log_dir, file)
                        try:
                            # Delete log files older than 30 days
                            if os.path.getmtime(file_path) < (datetime.now().timestamp() - 2592000):
                                file_size = os.path.getsize(file_path)
                                os.remove(file_path)
                                total_deleted += 1
                                total_size += file_size
                        except Exception as e:
                            logger.warning(f"Failed to delete log file {file_path}: {e}")
        
        logger.info(f"Cleaned up {total_deleted} log files ({total_size / 1024 / 1024:.2f} MB)")
        return {
            "status": "success", 
            "deleted_files": total_deleted, 
            "freed_space_mb": round(total_size / 1024 / 1024, 2)
        }
        
    except Exception as exc:
        logger.error(f"Failed to cleanup old logs: {exc}")
        raise self.retry(exc=exc, countdown=300)


@celery_app.task(bind=True)
def cleanup_old_notifications(self):
    """Clean up old notifications"""
    try:
        session_factory = get_session_factory()
        with session_factory() as db:
            # Delete notifications older than 90 days
            result = db.execute(text("""
                DELETE FROM notifications 
                WHERE created_at < NOW() - INTERVAL '90 days'
            """))
            
            deleted_count = result.rowcount
            db.commit()
            
            logger.info(f"Cleaned up {deleted_count} old notifications")
            return {"status": "success", "deleted_notifications": deleted_count}
            
    except Exception as exc:
        logger.error(f"Failed to cleanup old notifications: {exc}")
        raise self.retry(exc=exc, countdown=300)


@celery_app.task(bind=True)
def cleanup_old_system_events(self):
    """Clean up old system events"""
    try:
        session_factory = get_session_factory()
        with session_factory() as db:
            # Delete system events older than 1 year
            result = db.execute(text("""
                DELETE FROM system_events 
                WHERE created_at < NOW() - INTERVAL '1 year'
            """))
            
            deleted_count = result.rowcount
            db.commit()
            
            logger.info(f"Cleaned up {deleted_count} old system events")
            return {"status": "success", "deleted_events": deleted_count}
            
    except Exception as exc:
        logger.error(f"Failed to cleanup old system events: {exc}")
        raise self.retry(exc=exc, countdown=300)


@celery_app.task(bind=True)
def backup_database(self):
    """Create database backup"""
    try:
        if not settings.DATABASE_URL or settings.DATABASE_URL.startswith("sqlite"):
            logger.info("Skipping database backup for SQLite")
            return {"status": "skipped", "reason": "SQLite database"}
        
        # Create backup directory
        backup_dir = "backups"
        os.makedirs(backup_dir, exist_ok=True)
        
        # Generate backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{backup_dir}/maplehustlecan_backup_{timestamp}.sql"
        
        # Extract database connection details
        # This is a simplified version - in production, use proper database backup tools
        import subprocess
        
        # For PostgreSQL
        if settings.DATABASE_URL.startswith("postgresql"):
            cmd = [
                "pg_dump",
                settings.DATABASE_URL,
                "-f", backup_file,
                "--verbose"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                file_size = os.path.getsize(backup_file)
                logger.info(f"Database backup created: {backup_file} ({file_size / 1024 / 1024:.2f} MB)")
                
                # Compress backup
                compressed_file = f"{backup_file}.gz"
                subprocess.run(["gzip", backup_file])
                
                return {
                    "status": "success",
                    "backup_file": compressed_file,
                    "size_mb": round(file_size / 1024 / 1024, 2)
                }
            else:
                logger.error(f"Database backup failed: {result.stderr}")
                return {"status": "failed", "error": result.stderr}
        
        return {"status": "skipped", "reason": "Unsupported database type"}
        
    except Exception as exc:
        logger.error(f"Failed to backup database: {exc}")
        raise self.retry(exc=exc, countdown=3600)  # Retry in 1 hour


@celery_app.task(bind=True)
def cleanup_old_backups(self):
    """Clean up old database backups"""
    try:
        backup_dir = "backups"
        if not os.path.exists(backup_dir):
            return {"status": "skipped", "reason": "No backup directory"}
        
        total_deleted = 0
        total_size = 0
        
        for file in os.listdir(backup_dir):
            if file.endswith('.sql.gz'):
                file_path = os.path.join(backup_dir, file)
                try:
                    # Delete backup files older than 30 days
                    if os.path.getmtime(file_path) < (datetime.now().timestamp() - 2592000):
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        total_deleted += 1
                        total_size += file_size
                except Exception as e:
                    logger.warning(f"Failed to delete backup file {file_path}: {e}")
        
        logger.info(f"Cleaned up {total_deleted} old backup files ({total_size / 1024 / 1024:.2f} MB)")
        return {
            "status": "success", 
            "deleted_files": total_deleted, 
            "freed_space_mb": round(total_size / 1024 / 1024, 2)
        }
        
    except Exception as exc:
        logger.error(f"Failed to cleanup old backups: {exc}")
        raise self.retry(exc=exc, countdown=300)


@celery_app.task(bind=True)
def optimize_database(self):
    """Optimize database performance"""
    try:
        session_factory = get_session_factory()
        with session_factory() as db:
            # Run database-specific optimization commands
            if settings.DATABASE_URL.startswith("postgresql"):
                # PostgreSQL optimization
                db.execute(text("VACUUM ANALYZE"))
                db.execute(text("REINDEX DATABASE maplehustlecan"))
                
            elif settings.DATABASE_URL.startswith("sqlite"):
                # SQLite optimization
                db.execute(text("VACUUM"))
                db.execute(text("ANALYZE"))
            
            db.commit()
            
            logger.info("Database optimization completed")
            return {"status": "success", "message": "Database optimized"}
            
    except Exception as exc:
        logger.error(f"Failed to optimize database: {exc}")
        raise self.retry(exc=exc, countdown=3600)


@celery_app.task(bind=True)
def cleanup_cache(self):
    """Clean up Redis cache"""
    try:
        from app.core.cache import get_cache_manager
        
        cache_manager = get_cache_manager()
        if not cache_manager:
            return {"status": "skipped", "reason": "Cache not configured"}
        
        # Get cache info before cleanup
        info_before = await cache_manager.info()
        keys_before = info_before.get('db0', {}).get('keys', 0)
        
        # Clean up expired keys (Redis does this automatically, but we can force it)
        await cache_manager.client.execute_command("MEMORY PURGE")
        
        # Get cache info after cleanup
        info_after = await cache_manager.info()
        keys_after = info_after.get('db0', {}).get('keys', 0)
        
        cleaned_keys = keys_before - keys_after
        
        logger.info(f"Cache cleanup completed: {cleaned_keys} keys cleaned")
        return {
            "status": "success", 
            "keys_before": keys_before,
            "keys_after": keys_after,
            "cleaned_keys": cleaned_keys
        }
        
    except Exception as exc:
        logger.error(f"Failed to cleanup cache: {exc}")
        raise self.retry(exc=exc, countdown=300)
