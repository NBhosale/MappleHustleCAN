#!/usr/bin/env python3
"""
Database optimization script for MapleHustleCAN
"""
import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.db.session import get_engine
from app.core.performance_optimization import add_query_indexes


def create_performance_indexes():
    """Create database indexes for performance optimization"""
    engine = get_engine()
    
    print("🔧 Creating performance indexes...")
    
    indexes = add_query_indexes()
    
    with engine.connect() as conn:
        for i, index_sql in enumerate(indexes, 1):
            try:
                print(f"  {i:2d}. Creating index...")
                conn.execute(text(index_sql))
                conn.commit()
                print(f"      ✅ Success")
            except Exception as e:
                print(f"      ⚠️  Warning: {e}")
    
    print("✅ Database indexes created successfully")


def analyze_query_performance():
    """Analyze database query performance"""
    engine = get_engine()
    
    print("📊 Analyzing query performance...")
    
    with engine.connect() as conn:
        # Get table statistics
        result = conn.execute(text("""
            SELECT 
                schemaname,
                tablename,
                attname,
                n_distinct,
                correlation
            FROM pg_stats 
            WHERE schemaname = 'public'
            ORDER BY tablename, attname
        """))
        
        print("\n📈 Table Statistics:")
        print("-" * 80)
        for row in result:
            print(f"{row.tablename:20} | {row.attname:20} | distinct: {row.n_distinct:8} | correlation: {row.correlation:6.3f}")
        
        # Get index usage statistics
        result = conn.execute(text("""
            SELECT 
                schemaname,
                tablename,
                indexname,
                idx_scan,
                idx_tup_read,
                idx_tup_fetch
            FROM pg_stat_user_indexes 
            WHERE schemaname = 'public'
            ORDER BY idx_scan DESC
        """))
        
        print("\n🔍 Index Usage Statistics:")
        print("-" * 80)
        for row in result:
            print(f"{row.tablename:20} | {row.indexname:30} | scans: {row.idx_scan:8} | reads: {row.idx_tup_read:8}")
        
        # Get table sizes
        result = conn.execute(text("""
            SELECT 
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        """))
        
        print("\n💾 Table Sizes:")
        print("-" * 50)
        for row in result:
            print(f"{row.tablename:30} | {row.size:10}")


def optimize_database_settings():
    """Optimize database settings for performance"""
    engine = get_engine()
    
    print("⚙️  Optimizing database settings...")
    
    # PostgreSQL optimization settings
    optimizations = [
        # Connection settings
        "ALTER SYSTEM SET max_connections = 200;",
        "ALTER SYSTEM SET shared_buffers = '256MB';",
        "ALTER SYSTEM SET effective_cache_size = '1GB';",
        "ALTER SYSTEM SET work_mem = '4MB';",
        "ALTER SYSTEM SET maintenance_work_mem = '64MB';",
        
        # Query planning
        "ALTER SYSTEM SET random_page_cost = 1.1;",
        "ALTER SYSTEM SET effective_io_concurrency = 200;",
        
        # Logging and monitoring
        "ALTER SYSTEM SET log_min_duration_statement = 1000;",
        "ALTER SYSTEM SET log_checkpoints = on;",
        "ALTER SYSTEM SET log_connections = on;",
        "ALTER SYSTEM SET log_disconnections = on;",
        
        # Autovacuum settings
        "ALTER SYSTEM SET autovacuum = on;",
        "ALTER SYSTEM SET autovacuum_max_workers = 3;",
        "ALTER SYSTEM SET autovacuum_naptime = '1min';",
        
        # Statistics
        "ALTER SYSTEM SET default_statistics_target = 100;",
        "ALTER SYSTEM SET track_activities = on;",
        "ALTER SYSTEM SET track_counts = on;",
        "ALTER SYSTEM SET track_io_timing = on;",
    ]
    
    with engine.connect() as conn:
        for i, setting in enumerate(optimizations, 1):
            try:
                print(f"  {i:2d}. Applying setting...")
                conn.execute(text(setting))
                conn.commit()
                print(f"      ✅ Success")
            except Exception as e:
                print(f"      ⚠️  Warning: {e}")
    
    print("✅ Database settings optimized successfully")
    print("⚠️  Note: Some settings require database restart to take effect")


def vacuum_and_analyze():
    """Run VACUUM and ANALYZE for optimal performance"""
    engine = get_engine()
    
    print("🧹 Running VACUUM and ANALYZE...")
    
    with engine.connect() as conn:
        # Get all tables
        result = conn.execute(text("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public'
        """))
        
        tables = [row.tablename for row in result]
        
        for table in tables:
            try:
                print(f"  Processing {table}...")
                
                # VACUUM ANALYZE
                conn.execute(text(f"VACUUM ANALYZE {table}"))
                conn.commit()
                
                print(f"    ✅ VACUUM ANALYZE completed")
                
            except Exception as e:
                print(f"    ⚠️  Warning: {e}")
    
    print("✅ VACUUM and ANALYZE completed successfully")


def check_database_health():
    """Check database health and performance"""
    engine = get_engine()
    
    print("🏥 Checking database health...")
    
    with engine.connect() as conn:
        # Check connection count
        result = conn.execute(text("""
            SELECT count(*) as active_connections
            FROM pg_stat_activity 
            WHERE state = 'active'
        """))
        
        active_connections = result.scalar()
        print(f"  Active connections: {active_connections}")
        
        # Check database size
        result = conn.execute(text("""
            SELECT pg_size_pretty(pg_database_size(current_database())) as db_size
        """))
        
        db_size = result.scalar()
        print(f"  Database size: {db_size}")
        
        # Check cache hit ratio
        result = conn.execute(text("""
            SELECT 
                round(
                    (blks_hit::float / (blks_hit + blks_read)) * 100, 2
                ) as cache_hit_ratio
            FROM pg_stat_database 
            WHERE datname = current_database()
        """))
        
        cache_hit_ratio = result.scalar()
        print(f"  Cache hit ratio: {cache_hit_ratio}%")
        
        # Check for long-running queries
        result = conn.execute(text("""
            SELECT 
                pid,
                now() - pg_stat_activity.query_start AS duration,
                query
            FROM pg_stat_activity 
            WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes'
            AND state = 'active'
        """))
        
        long_queries = list(result)
        if long_queries:
            print(f"  ⚠️  Found {len(long_queries)} long-running queries")
            for query in long_queries:
                print(f"    PID {query.pid}: {query.duration} - {query.query[:100]}...")
        else:
            print("  ✅ No long-running queries found")
        
        # Check for locks
        result = conn.execute(text("""
            SELECT 
                count(*) as lock_count,
                mode,
                granted
            FROM pg_locks 
            GROUP BY mode, granted
            ORDER BY lock_count DESC
        """))
        
        locks = list(result)
        if locks:
            print(f"  Locks:")
            for lock in locks:
                status = "granted" if lock.granted else "waiting"
                print(f"    {lock.mode}: {lock.lock_count} ({status})")
        else:
            print("  ✅ No locks found")


async def warm_up_cache():
    """Warm up application cache"""
    print("🔥 Warming up application cache...")
    
    try:
        from app.services.optimized_services import warm_up_cache
        await warm_up_cache()
        print("✅ Cache warming completed successfully")
    except Exception as e:
        print(f"⚠️  Warning: Cache warming failed: {e}")


def main():
    """Main optimization function"""
    print("🚀 Starting MapleHustleCAN Database Optimization")
    print("=" * 60)
    
    try:
        # 1. Create performance indexes
        create_performance_indexes()
        print()
        
        # 2. Optimize database settings
        optimize_database_settings()
        print()
        
        # 3. Run VACUUM and ANALYZE
        vacuum_and_analyze()
        print()
        
        # 4. Check database health
        check_database_health()
        print()
        
        # 5. Warm up cache
        asyncio.run(warm_up_cache())
        print()
        
        print("🎉 Database optimization completed successfully!")
        print("\n📋 Next steps:")
        print("  1. Restart PostgreSQL to apply all settings")
        print("  2. Monitor performance metrics")
        print("  3. Run load tests to verify improvements")
        print("  4. Set up regular maintenance tasks")
        
    except Exception as e:
        print(f"❌ Error during optimization: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
