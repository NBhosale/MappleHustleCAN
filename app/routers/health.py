"""
Health check endpoints for MapleHustleCAN
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
import asyncio
import time
from datetime import datetime
from typing import Dict, Any
import psutil
import os

from app.db import get_db
from app.core.config import settings

router = APIRouter(prefix="/health", tags=["Health"])


class HealthChecker:
    """Health check utilities"""
    
    def __init__(self):
        self.start_time = time.time()
    
    def get_uptime(self) -> float:
        """Get application uptime in seconds"""
        return time.time() - self.start_time
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None
        }
    
    async def check_database(self, db: Session) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        try:
            start_time = time.time()
            result = db.execute(text("SELECT 1"))
            response_time = time.time() - start_time
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time * 1000, 2),
                "connection_pool": {
                    "size": db.bind.pool.size(),
                    "checked_in": db.bind.pool.checkedin(),
                    "checked_out": db.bind.pool.checkedout(),
                    "overflow": db.bind.pool.overflow(),
                    "invalid": db.bind.pool.invalid()
                }
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "response_time_ms": None
            }
    
    async def check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity"""
        try:
            import redis
            from app.core.config import settings
            
            if not settings.REDIS_URL:
                return {
                    "status": "not_configured",
                    "message": "Redis not configured"
                }
            
            r = redis.from_url(settings.REDIS_URL)
            start_time = time.time()
            r.ping()
            response_time = time.time() - start_time
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time * 1000, 2),
                "info": r.info()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "response_time_ms": None
            }
    
    async def check_external_services(self) -> Dict[str, Any]:
        """Check external services"""
        services = {}
        
        # Check email service
        if settings.SMTP_HOST:
            try:
                import smtplib
                start_time = time.time()
                server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
                server.quit()
                response_time = time.time() - start_time
                
                services["email"] = {
                    "status": "healthy",
                    "response_time_ms": round(response_time * 1000, 2)
                }
            except Exception as e:
                services["email"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        else:
            services["email"] = {
                "status": "not_configured",
                "message": "SMTP not configured"
            }
        
        # Check S3 service
        if settings.S3_BUCKET:
            try:
                import boto3
                start_time = time.time()
                s3 = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_REGION
                )
                s3.head_bucket(Bucket=settings.S3_BUCKET)
                response_time = time.time() - start_time
                
                services["s3"] = {
                    "status": "healthy",
                    "response_time_ms": round(response_time * 1000, 2)
                }
            except Exception as e:
                services["s3"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        else:
            services["s3"] = {
                "status": "not_configured",
                "message": "S3 not configured"
            }
        
        return services


health_checker = HealthChecker()


@router.get("/")
def health_check():
    """
    Basic health check endpoint
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": health_checker.get_uptime(),
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }


@router.get("/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness check - verifies the application is ready to serve traffic
    """
    checks = {}
    overall_status = "healthy"
    
    # Check database
    db_check = await health_checker.check_database(db)
    checks["database"] = db_check
    if db_check["status"] != "healthy":
        overall_status = "unhealthy"
    
    # Check Redis
    redis_check = await health_checker.check_redis()
    checks["redis"] = redis_check
    if redis_check["status"] not in ["healthy", "not_configured"]:
        overall_status = "degraded"
    
    # Check external services
    external_checks = await health_checker.check_external_services()
    checks["external_services"] = external_checks
    
    # Determine overall status
    unhealthy_services = [
        service for service in external_checks.values()
        if service["status"] == "unhealthy"
    ]
    if unhealthy_services:
        overall_status = "degraded"
    
    status_code = 200 if overall_status == "healthy" else 503
    
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks,
        "uptime_seconds": health_checker.get_uptime(),
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }


@router.get("/live")
def liveness_check():
    """
    Liveness check - verifies the application is alive
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": health_checker.get_uptime(),
        "pid": os.getpid()
    }


@router.get("/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """
    Detailed health check with system metrics
    """
    checks = {}
    overall_status = "healthy"
    
    # System information
    system_info = health_checker.get_system_info()
    checks["system"] = {
        "status": "healthy" if system_info["cpu_percent"] < 90 and system_info["memory_percent"] < 90 else "degraded",
        "metrics": system_info
    }
    
    # Database check
    db_check = await health_checker.check_database(db)
    checks["database"] = db_check
    if db_check["status"] != "healthy":
        overall_status = "unhealthy"
    
    # Redis check
    redis_check = await health_checker.check_redis()
    checks["redis"] = redis_check
    if redis_check["status"] not in ["healthy", "not_configured"]:
        overall_status = "degraded"
    
    # External services
    external_checks = await health_checker.check_external_services()
    checks["external_services"] = external_checks
    
    # Application metrics
    checks["application"] = {
        "status": "healthy",
        "uptime_seconds": health_checker.get_uptime(),
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG
    }
    
    # Determine overall status
    if any(check.get("status") == "unhealthy" for check in checks.values() if isinstance(check, dict)):
        overall_status = "unhealthy"
    elif any(check.get("status") == "degraded" for check in checks.values() if isinstance(check, dict)):
        overall_status = "degraded"
    
    status_code = 200 if overall_status == "healthy" else 503
    
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks,
        "summary": {
            "total_checks": len(checks),
            "healthy": len([c for c in checks.values() if isinstance(c, dict) and c.get("status") == "healthy"]),
            "degraded": len([c for c in checks.values() if isinstance(c, dict) and c.get("status") == "degraded"]),
            "unhealthy": len([c for c in checks.values() if isinstance(c, dict) and c.get("status") == "unhealthy"])
        }
    }


@router.get("/metrics")
def metrics():
    """
    Application metrics endpoint
    """
    system_info = health_checker.get_system_info()
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": health_checker.get_uptime(),
        "system": system_info,
        "application": {
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG
        }
    }


@router.get("/version")
def version_info():
    """
    Version information endpoint
    """
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "build_time": datetime.utcnow().isoformat(),
        "features": {
            "cors_enabled": bool(settings.ALLOWED_ORIGINS),
            "redis_enabled": bool(settings.REDIS_URL),
            "s3_enabled": bool(settings.S3_BUCKET),
            "email_enabled": bool(settings.SMTP_HOST),
            "security_monitoring": settings.SECURITY_MONITORING_ENABLED
        }
    }
