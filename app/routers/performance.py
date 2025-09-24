"""
Performance monitoring and optimization endpoints
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.performance_optimization import (
    get_performance_optimizer,
    get_performance_metrics,
    warm_cache
)
from app.utils.deps import require_admin

router = APIRouter(prefix="/performance", tags=["Performance"])


@router.get("/metrics")
async def get_performance_metrics_endpoint():
    """
    Get comprehensive performance metrics
    """
    try:
        metrics = await get_performance_metrics()
        return {
            "success": True,
            "data": metrics,
            "message": "Performance metrics retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve performance metrics: {str(e)}"
        )


@router.get("/cache/stats")
async def get_cache_stats():
    """
    Get cache performance statistics
    """
    try:
        optimizer = get_performance_optimizer()
        cache_stats = optimizer.get_cache_stats()
        
        return {
            "success": True,
            "data": {
                "cache_stats": cache_stats,
                "cache_enabled": optimizer.cache_manager is not None,
                "cache_manager_type": type(optimizer.cache_manager).__name__ if optimizer.cache_manager else None
            },
            "message": "Cache statistics retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve cache statistics: {str(e)}"
        )


@router.get("/query/stats")
async def get_query_stats():
    """
    Get database query performance statistics
    """
    try:
        optimizer = get_performance_optimizer()
        query_stats = optimizer.get_query_stats()
        
        return {
            "success": True,
            "data": {
                "query_stats": query_stats,
                "total_operations": sum(stats.get("total_calls", 0) for stats in query_stats.values()),
                "average_response_time": sum(stats.get("avg_time", 0) for stats in query_stats.values()) / len(query_stats) if query_stats else 0
            },
            "message": "Query statistics retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve query statistics: {str(e)}"
        )


@router.post("/cache/warm")
async def warm_cache_endpoint(current_user=Depends(require_admin)):
    """
    Warm up application cache (Admin only)
    """
    try:
        await warm_cache()
        return {
            "success": True,
            "message": "Cache warming completed successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to warm cache: {str(e)}"
        )


@router.delete("/cache/clear")
async def clear_cache_endpoint(current_user=Depends(require_admin)):
    """
    Clear application cache (Admin only)
    """
    try:
        optimizer = get_performance_optimizer()
        if optimizer.cache_manager:
            await optimizer.cache_manager.flushdb()
            return {
                "success": True,
                "message": "Cache cleared successfully"
            }
        else:
            return {
                "success": True,
                "message": "No cache manager available"
            }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear cache: {str(e)}"
        )


@router.get("/database/health")
async def get_database_health(db: Session = Depends(get_db)):
    """
    Get database health and performance metrics
    """
    try:
        # Get database connection info
        result = db.execute("SELECT version()").scalar()
        db_version = result.split('\n')[0] if result else "Unknown"
        
        # Get connection count
        result = db.execute("""
            SELECT count(*) as active_connections
            FROM pg_stat_activity 
            WHERE state = 'active'
        """).scalar()
        active_connections = result or 0
        
        # Get database size
        result = db.execute("""
            SELECT pg_size_pretty(pg_database_size(current_database())) as db_size
        """).scalar()
        db_size = result or "Unknown"
        
        # Get cache hit ratio
        result = db.execute("""
            SELECT 
                round(
                    (blks_hit::float / (blks_hit + blks_read)) * 100, 2
                ) as cache_hit_ratio
            FROM pg_stat_database 
            WHERE datname = current_database()
        """).scalar()
        cache_hit_ratio = result or 0
        
        # Get table statistics
        result = db.execute("""
            SELECT 
                schemaname,
                tablename,
                n_tup_ins as inserts,
                n_tup_upd as updates,
                n_tup_del as deletes
            FROM pg_stat_user_tables 
            WHERE schemaname = 'public'
            ORDER BY n_tup_ins + n_tup_upd + n_tup_del DESC
            LIMIT 10
        """)
        
        table_stats = [
            {
                "table": row.tablename,
                "inserts": row.inserts,
                "updates": row.updates,
                "deletes": row.deletes
            }
            for row in result
        ]
        
        return {
            "success": True,
            "data": {
                "database_version": db_version,
                "active_connections": active_connections,
                "database_size": db_size,
                "cache_hit_ratio": f"{cache_hit_ratio}%",
                "table_stats": table_stats
            },
            "message": "Database health retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve database health: {str(e)}"
        )


@router.get("/optimization/recommendations")
async def get_optimization_recommendations(db: Session = Depends(get_db)):
    """
    Get performance optimization recommendations
    """
    try:
        recommendations = []
        
        # Check cache hit ratio
        result = db.execute("""
            SELECT 
                round(
                    (blks_hit::float / (blks_hit + blks_read)) * 100, 2
                ) as cache_hit_ratio
            FROM pg_stat_database 
            WHERE datname = current_database()
        """).scalar()
        
        cache_hit_ratio = result or 0
        if cache_hit_ratio < 90:
            recommendations.append({
                "type": "warning",
                "category": "database",
                "title": "Low Cache Hit Ratio",
                "description": f"Database cache hit ratio is {cache_hit_ratio}%. Consider increasing shared_buffers.",
                "priority": "high"
            })
        
        # Check for missing indexes
        result = db.execute("""
            SELECT 
                schemaname,
                tablename,
                attname,
                n_distinct,
                correlation
            FROM pg_stats 
            WHERE schemaname = 'public'
            AND n_distinct > 100
            AND correlation < 0.1
            ORDER BY n_distinct DESC
        """)
        
        missing_indexes = list(result)
        if missing_indexes:
            recommendations.append({
                "type": "info",
                "category": "database",
                "title": "Potential Missing Indexes",
                "description": f"Found {len(missing_indexes)} columns that might benefit from indexes.",
                "priority": "medium",
                "details": [
                    f"{row.tablename}.{row.attname} (distinct: {row.n_distinct})"
                    for row in missing_indexes[:5]
                ]
            })
        
        # Check for long-running queries
        result = db.execute("""
            SELECT 
                pid,
                now() - pg_stat_activity.query_start AS duration,
                query
            FROM pg_stat_activity 
            WHERE (now() - pg_stat_activity.query_start) > interval '1 minute'
            AND state = 'active'
        """)
        
        long_queries = list(result)
        if long_queries:
            recommendations.append({
                "type": "warning",
                "category": "database",
                "title": "Long-Running Queries",
                "description": f"Found {len(long_queries)} queries running for more than 1 minute.",
                "priority": "high",
                "details": [
                    f"PID {query.pid}: {query.duration} - {query.query[:100]}..."
                    for query in long_queries[:3]
                ]
            })
        
        # Check application cache
        optimizer = get_performance_optimizer()
        if not optimizer.cache_manager:
            recommendations.append({
                "type": "info",
                "category": "application",
                "title": "Cache Not Enabled",
                "description": "Application cache is not enabled. Consider enabling Redis for better performance.",
                "priority": "medium"
            })
        else:
            cache_stats = optimizer.get_cache_stats()
            if cache_stats:
                avg_hit_rate = sum(
                    stats.get("hit_rate", 0) for stats in cache_stats.values()
                ) / len(cache_stats)
                
                if avg_hit_rate < 50:
                    recommendations.append({
                        "type": "warning",
                        "category": "application",
                        "title": "Low Cache Hit Rate",
                        "description": f"Application cache hit rate is {avg_hit_rate:.1f}%. Consider adjusting cache strategies.",
                        "priority": "medium"
                    })
        
        return {
            "success": True,
            "data": {
                "recommendations": recommendations,
                "total_recommendations": len(recommendations),
                "high_priority": len([r for r in recommendations if r["priority"] == "high"]),
                "medium_priority": len([r for r in recommendations if r["priority"] == "medium"]),
                "low_priority": len([r for r in recommendations if r["priority"] == "low"])
            },
            "message": "Optimization recommendations retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve optimization recommendations: {str(e)}"
        )


@router.get("/status")
async def get_performance_status():
    """
    Get overall performance status
    """
    try:
        optimizer = get_performance_optimizer()
        
        # Get basic metrics
        cache_stats = optimizer.get_cache_stats()
        query_stats = optimizer.get_query_stats()
        
        # Calculate overall status
        status = "healthy"
        issues = []
        
        # Check cache status
        if not optimizer.cache_manager:
            status = "degraded"
            issues.append("Cache not enabled")
        elif cache_stats:
            avg_hit_rate = sum(
                stats.get("hit_rate", 0) for stats in cache_stats.values()
            ) / len(cache_stats)
            if avg_hit_rate < 50:
                status = "degraded"
                issues.append(f"Low cache hit rate: {avg_hit_rate:.1f}%")
        
        # Check query performance
        if query_stats:
            avg_response_time = sum(
                stats.get("avg_time", 0) for stats in query_stats.values()
            ) / len(query_stats)
            if avg_response_time > 1.0:  # More than 1 second
                status = "degraded"
                issues.append(f"Slow queries: {avg_response_time:.2f}s average")
        
        return {
            "success": True,
            "data": {
                "status": status,
                "issues": issues,
                "cache_enabled": optimizer.cache_manager is not None,
                "cache_operations": len(cache_stats),
                "query_operations": len(query_stats),
                "timestamp": "2024-01-01T00:00:00Z"  # This would be actual timestamp
            },
            "message": "Performance status retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve performance status: {str(e)}"
        )
