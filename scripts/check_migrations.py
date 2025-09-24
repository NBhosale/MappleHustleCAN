#!/usr/bin/env python3
"""
Migration drift checker for MapleHustleCAN
Ensures Alembic migrations are in sync with SQL schema
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path
from sqlalchemy import create_engine, text
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import settings


def check_migration_drift():
    """Check if migrations are in sync with database schema"""
    print("🔍 Checking migration drift...")
    
    # Create temporary database
    temp_db_url = "sqlite:///temp_migration_check.db"
    engine = create_engine(temp_db_url)
    
    try:
        # Run all migrations
        print("📦 Running all migrations...")
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", temp_db_url)
        
        # Upgrade to head
        command.upgrade(alembic_cfg, "head")
        
        # Check current revision
        with engine.connect() as conn:
            context = MigrationContext.configure(conn)
            current_rev = context.get_current_revision()
            print(f"✅ Current revision: {current_rev}")
        
        # Check if there are any pending migrations
        script_dir = ScriptDirectory.from_config(alembic_cfg)
        head_rev = script_dir.get_current_head()
        
        if current_rev != head_rev:
            print(f"❌ Migration drift detected!")
            print(f"   Current: {current_rev}")
            print(f"   Head: {head_rev}")
            return False
        
        print("✅ No migration drift detected")
        return True
        
    except Exception as e:
        print(f"❌ Error checking migrations: {e}")
        return False
    
    finally:
        # Clean up temporary database
        if os.path.exists("temp_migration_check.db"):
            os.remove("temp_migration_check.db")


def check_migration_reversibility():
    """Check if migrations can be reversed"""
    print("🔄 Checking migration reversibility...")
    
    temp_db_url = "sqlite:///temp_reversibility_check.db"
    engine = create_engine(temp_db_url)
    
    try:
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", temp_db_url)
        
        # Get all migration revisions
        script_dir = ScriptDirectory.from_config(alembic_cfg)
        revisions = list(script_dir.walk_revisions())
        
        print(f"📋 Found {len(revisions)} migrations to test")
        
        # Test each migration
        for i, revision in enumerate(revisions):
            print(f"🔄 Testing migration {i+1}/{len(revisions)}: {revision.revision}")
            
            try:
                # Upgrade to this revision
                command.upgrade(alembic_cfg, revision.revision)
                
                # Downgrade to previous revision
                if i < len(revisions) - 1:
                    prev_revision = revisions[i + 1].revision
                    command.downgrade(alembic_cfg, prev_revision)
                    
                    # Upgrade back to current
                    command.upgrade(alembic_cfg, revision.revision)
                
                print(f"✅ Migration {revision.revision} is reversible")
                
            except Exception as e:
                print(f"❌ Migration {revision.revision} failed reversibility test: {e}")
                return False
        
        print("✅ All migrations are reversible")
        return True
        
    except Exception as e:
        print(f"❌ Error checking reversibility: {e}")
        return False
    
    finally:
        # Clean up temporary database
        if os.path.exists("temp_reversibility_check.db"):
            os.remove("temp_reversibility_check.db")


def check_migration_sql_syntax():
    """Check if migration SQL syntax is valid"""
    print("📝 Checking migration SQL syntax...")
    
    try:
        # Get all migration files
        migration_dir = Path("alembic/versions")
        migration_files = list(migration_dir.glob("*.py"))
        
        print(f"📋 Found {len(migration_files)} migration files")
        
        for migration_file in migration_files:
            print(f"🔍 Checking {migration_file.name}...")
            
            try:
                # Try to compile the migration file
                with open(migration_file, 'r') as f:
                    content = f.read()
                
                compile(content, str(migration_file), 'exec')
                print(f"✅ {migration_file.name} syntax is valid")
                
            except SyntaxError as e:
                print(f"❌ {migration_file.name} has syntax error: {e}")
                return False
            except Exception as e:
                print(f"❌ {migration_file.name} has error: {e}")
                return False
        
        print("✅ All migration files have valid syntax")
        return True
        
    except Exception as e:
        print(f"❌ Error checking migration syntax: {e}")
        return False


def main():
    """Run all migration checks"""
    print("🚀 Starting migration checks...")
    
    checks = [
        ("Migration Drift", check_migration_drift),
        ("Migration Reversibility", check_migration_reversibility),
        ("Migration SQL Syntax", check_migration_sql_syntax),
    ]
    
    results = []
    
    for check_name, check_func in checks:
        print(f"\n{'='*50}")
        print(f"Running: {check_name}")
        print('='*50)
        
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ {check_name} failed with error: {e}")
            results.append((check_name, False))
    
    # Summary
    print(f"\n{'='*50}")
    print("MIGRATION CHECK SUMMARY")
    print('='*50)
    
    all_passed = True
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{check_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All migration checks passed!")
        sys.exit(0)
    else:
        print("\n💥 Some migration checks failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
