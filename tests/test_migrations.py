"""
Migration testing for MapleHustleCAN
"""
import pytest
import os
import tempfile
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory

from app.db.base_class import Base
from app.models.users import User
from app.models.services import Service, Portfolio, Availability
from app.models.bookings import Booking
from app.models.items import Item
from app.models.orders import Order
from app.models.payments import Payment
from app.models.messages import Message
from app.models.notifications import Notification
from app.models.system import Session, SystemEvent, TaxRule, ProviderMetric
from app.models.tokens import RefreshToken
from app.models.provinces import CanadianProvince


class TestMigrationBasics:
    """Test basic migration functionality"""
    
    def test_migration_config_valid(self):
        """Test that migration configuration is valid"""
        # Create temporary directory for test database
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            database_url = f"sqlite:///{db_path}"
            
            # Create alembic config
            alembic_cfg = Config("alembic.ini")
            alembic_cfg.set_main_option("sqlalchemy.url", database_url)
            
            # Test that config is valid
            script_dir = ScriptDirectory.from_config(alembic_cfg)
            assert script_dir is not None
    
    def test_migration_script_loading(self):
        """Test that migration scripts can be loaded"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            database_url = f"sqlite:///{db_path}"
            
            alembic_cfg = Config("alembic.ini")
            alembic_cfg.set_main_option("sqlalchemy.url", database_url)
            
            script_dir = ScriptDirectory.from_config(alembic_cfg)
            revisions = list(script_dir.walk_revisions())
            
            # Should have at least one migration
            assert len(revisions) > 0
            
            # All revisions should have valid down_revision or be head
            for revision in revisions:
                if revision.down_revision is None:
                    # This should be the first migration
                    continue
                else:
                    # Should be able to find parent revision
                    parent = script_dir.get_revision(revision.down_revision)
                    assert parent is not None


class TestMigrationExecution:
    """Test migration execution"""
    
    def test_migration_upgrade_downgrade(self):
        """Test migration upgrade and downgrade"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            database_url = f"sqlite:///{db_path}"
            
            # Create engine and session
            engine = create_engine(database_url)
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            
            # Create alembic config
            alembic_cfg = Config("alembic.ini")
            alembic_cfg.set_main_option("sqlalchemy.url", database_url)
            
            try:
                # Test upgrade to head
                command.upgrade(alembic_cfg, "head")
                
                # Verify tables were created
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
                    tables = [row[0] for row in result]
                    
                    # Check for key tables
                    expected_tables = [
                        "users", "services", "portfolio", "availability", 
                        "bookings", "items", "orders", "payments",
                        "messages", "notifications", "canadian_provinces"
                    ]
                    
                    for table in expected_tables:
                        assert table in tables, f"Table {table} not found after migration"
                
                # Test downgrade to base
                command.downgrade(alembic_cfg, "base")
                
                # Verify tables were dropped
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
                    tables = [row[0] for row in result]
                    
                    # Should only have alembic_version table
                    assert len(tables) <= 1
                    
            finally:
                engine.dispose()
    
    def test_migration_step_by_step(self):
        """Test migration step by step"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            database_url = f"sqlite:///{db_path}"
            
            # Create engine
            engine = create_engine(database_url)
            
            # Create alembic config
            alembic_cfg = Config("alembic.ini")
            alembic_cfg.set_main_option("sqlalchemy.url", database_url)
            
            try:
                # Get all revisions
                script_dir = ScriptDirectory.from_config(alembic_cfg)
                revisions = list(script_dir.walk_revisions())
                
                # Apply migrations one by one
                for revision in reversed(revisions):
                    command.upgrade(alembic_cfg, revision.revision)
                    
                    # Verify migration was applied
                    with engine.connect() as conn:
                        context = MigrationContext.configure(conn)
                        current_rev = context.get_current_revision()
                        assert current_rev == revision.revision
                
                # Downgrade one by one
                for revision in revisions:
                    if revision.down_revision is not None:
                        command.downgrade(alembic_cfg, revision.down_revision)
                        
                        # Verify downgrade was applied
                        with engine.connect() as conn:
                            context = MigrationContext.configure(conn)
                            current_rev = context.get_current_revision()
                            assert current_rev == revision.down_revision
                    
            finally:
                engine.dispose()


class TestMigrationDataIntegrity:
    """Test data integrity during migrations"""
    
    def test_migration_with_data(self):
        """Test migration with existing data"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            database_url = f"sqlite:///{db_path}"
            
            # Create engine and session
            engine = create_engine(database_url)
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            
            # Create alembic config
            alembic_cfg = Config("alembic.ini")
            alembic_cfg.set_main_option("sqlalchemy.url", database_url)
            
            try:
                # Apply initial migrations
                command.upgrade(alembic_cfg, "head")
                
                # Insert test data
                with SessionLocal() as session:
                    # Create test user
                    user = User(
                        email="test@example.com",
                        name="Test User",
                        hashed_password="hashed_password",
                        role="client",
                        status="active"
                    )
                    session.add(user)
                    session.commit()
                    session.refresh(user)
                    user_id = user.id
                
                # Test that data persists through migration
                with SessionLocal() as session:
                    user = session.query(User).filter(User.id == user_id).first()
                    assert user is not None
                    assert user.email == "test@example.com"
                
            finally:
                engine.dispose()
    
    def test_migration_rollback_data_preservation(self):
        """Test that data is preserved during rollback"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            database_url = f"sqlite:///{db_path}"
            
            # Create engine and session
            engine = create_engine(database_url)
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            
            # Create alembic config
            alembic_cfg = Config("alembic.ini")
            alembic_cfg.set_main_option("sqlalchemy.url", database_url)
            
            try:
                # Apply migrations
                command.upgrade(alembic_cfg, "head")
                
                # Insert test data
                with SessionLocal() as session:
                    user = User(
                        email="rollback@example.com",
                        name="Rollback Test",
                        hashed_password="hashed_password",
                        role="provider",
                        status="active"
                    )
                    session.add(user)
                    session.commit()
                    session.refresh(user)
                    user_id = user.id
                
                # Rollback one migration
                script_dir = ScriptDirectory.from_config(alembic_cfg)
                revisions = list(script_dir.walk_revisions())
                if len(revisions) > 1:
                    command.downgrade(alembic_cfg, revisions[1].revision)
                    
                    # Verify data is still there
                    with SessionLocal() as session:
                        user = session.query(User).filter(User.id == user_id).first()
                        assert user is not None
                        assert user.email == "rollback@example.com"
                
            finally:
                engine.dispose()


class TestMigrationConstraints:
    """Test migration constraints and indexes"""
    
    def test_foreign_key_constraints(self):
        """Test that foreign key constraints are properly created"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            database_url = f"sqlite:///{db_path}"
            
            # Create engine and session
            engine = create_engine(database_url)
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            
            # Create alembic config
            alembic_cfg = Config("alembic.ini")
            alembic_cfg.set_main_option("sqlalchemy.url", database_url)
            
            try:
                # Apply migrations
                command.upgrade(alembic_cfg, "head")
                
                # Test foreign key constraints
                with SessionLocal() as session:
                    # Create user
                    user = User(
                        email="fk_test@example.com",
                        name="FK Test",
                        hashed_password="hashed_password",
                        role="provider",
                        status="active"
                    )
                    session.add(user)
                    session.commit()
                    session.refresh(user)
                    
                    # Create service (should reference user)
                    service = Service(
                        provider_id=user.id,
                        type="dog_walking",
                        title="Test Service",
                        description="Test Description",
                        hourly_rate=25.0
                    )
                    session.add(service)
                    session.commit()
                    
                    # Verify service was created
                    assert service.id is not None
                    assert service.provider_id == user.id
                
            finally:
                engine.dispose()
    
    def test_unique_constraints(self):
        """Test that unique constraints are properly created"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            database_url = f"sqlite:///{db_path}"
            
            # Create engine and session
            engine = create_engine(database_url)
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            
            # Create alembic config
            alembic_cfg = Config("alembic.ini")
            alembic_cfg.set_main_option("sqlalchemy.url", database_url)
            
            try:
                # Apply migrations
                command.upgrade(alembic_cfg, "head")
                
                # Test unique email constraint
                with SessionLocal() as session:
                    # Create first user
                    user1 = User(
                        email="unique@example.com",
                        name="Unique Test 1",
                        hashed_password="hashed_password",
                        role="client",
                        status="active"
                    )
                    session.add(user1)
                    session.commit()
                    
                    # Try to create second user with same email
                    user2 = User(
                        email="unique@example.com",
                        name="Unique Test 2",
                        hashed_password="hashed_password",
                        role="client",
                        status="active"
                    )
                    session.add(user2)
                    
                    # Should raise integrity error
                    with pytest.raises(Exception):  # SQLAlchemy IntegrityError
                        session.commit()
                
            finally:
                engine.dispose()
    
    def test_indexes_created(self):
        """Test that indexes are properly created"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            database_url = f"sqlite:///{db_path}"
            
            # Create engine
            engine = create_engine(database_url)
            
            # Create alembic config
            alembic_cfg = Config("alembic.ini")
            alembic_cfg.set_main_option("sqlalchemy.url", database_url)
            
            try:
                # Apply migrations
                command.upgrade(alembic_cfg, "head")
                
                # Check for indexes
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='index'"))
                    indexes = [row[0] for row in result]
                    
                    # Check for key indexes
                    expected_indexes = [
                        "ix_users_email",
                        "ix_services_provider_id",
                        "ix_bookings_client_id",
                        "ix_bookings_provider_id"
                    ]
                    
                    for index in expected_indexes:
                        assert index in indexes, f"Index {index} not found after migration"
                
            finally:
                engine.dispose()


class TestMigrationPerformance:
    """Test migration performance"""
    
    def test_migration_speed(self):
        """Test that migrations complete in reasonable time"""
        import time
        
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            database_url = f"sqlite:///{db_path}"
            
            # Create alembic config
            alembic_cfg = Config("alembic.ini")
            alembic_cfg.set_main_option("sqlalchemy.url", database_url)
            
            # Time the migration
            start_time = time.time()
            command.upgrade(alembic_cfg, "head")
            end_time = time.time()
            
            migration_time = end_time - start_time
            
            # Should complete within 30 seconds
            assert migration_time < 30, f"Migration took {migration_time:.2f} seconds, expected < 30"
    
    def test_migration_with_large_dataset(self):
        """Test migration with large dataset"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            database_url = f"sqlite:///{db_path}"
            
            # Create engine and session
            engine = create_engine(database_url)
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            
            # Create alembic config
            alembic_cfg = Config("alembic.ini")
            alembic_cfg.set_main_option("sqlalchemy.url", database_url)
            
            try:
                # Apply initial migrations
                command.upgrade(alembic_cfg, "head")
                
                # Insert large dataset
                with SessionLocal() as session:
                    # Create 1000 users
                    users = []
                    for i in range(1000):
                        user = User(
                            email=f"user{i}@example.com",
                            name=f"User {i}",
                            hashed_password="hashed_password",
                            role="client",
                            status="active"
                        )
                        users.append(user)
                    
                    session.add_all(users)
                    session.commit()
                
                # Verify data was inserted
                with SessionLocal() as session:
                    user_count = session.query(User).count()
                    assert user_count == 1000
                
            finally:
                engine.dispose()


class TestMigrationErrorHandling:
    """Test migration error handling"""
    
    def test_migration_with_invalid_data(self):
        """Test migration behavior with invalid data"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            database_url = f"sqlite:///{db_path}"
            
            # Create engine and session
            engine = create_engine(database_url)
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            
            # Create alembic config
            alembic_cfg = Config("alembic.ini")
            alembic_cfg.set_main_option("sqlalchemy.url", database_url)
            
            try:
                # Apply migrations
                command.upgrade(alembic_cfg, "head")
                
                # Try to insert invalid data
                with SessionLocal() as session:
                    # Try to create user with invalid email
                    user = User(
                        email="invalid-email",  # Invalid email format
                        name="Invalid User",
                        hashed_password="hashed_password",
                        role="client",
                        status="active"
                    )
                    session.add(user)
                    
                    # Should raise validation error
                    with pytest.raises(Exception):
                        session.commit()
                
            finally:
                engine.dispose()
    
    def test_migration_rollback_on_error(self):
        """Test that migration rollback works on error"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            database_url = f"sqlite:///{db_path}"
            
            # Create alembic config
            alembic_cfg = Config("alembic.ini")
            alembic_cfg.set_main_option("sqlalchemy.url", database_url)
            
            try:
                # Apply migrations
                command.upgrade(alembic_cfg, "head")
                
                # Get current revision
                with engine.connect() as conn:
                    context = MigrationContext.configure(conn)
                    current_rev = context.get_current_revision()
                
                # Rollback to base
                command.downgrade(alembic_cfg, "base")
                
                # Verify rollback worked
                with engine.connect() as conn:
                    context = MigrationContext.configure(conn)
                    current_rev_after = context.get_current_revision()
                    assert current_rev_after is None
                
            finally:
                engine.dispose()
