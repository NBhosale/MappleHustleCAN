#!/usr/bin/env python3
"""
Database seeding script for MapleHustleCAN
Creates initial data: provinces, roles, admin user, etc.
"""

import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from passlib.context import CryptContext
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import settings
from app.models.users import User, UserRole, UserStatus
from app.models.provinces import CanadianProvince

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def seed_canadian_provinces(session):
    """Seed Canadian provinces data"""
    print("🌿 Seeding Canadian provinces...")
    
    provinces_data = [
        ("AB", "Alberta"),
        ("BC", "British Columbia"),
        ("MB", "Manitoba"),
        ("NB", "New Brunswick"),
        ("NL", "Newfoundland and Labrador"),
        ("NS", "Nova Scotia"),
        ("NT", "Northwest Territories"),
        ("NU", "Nunavut"),
        ("ON", "Ontario"),
        ("PE", "Prince Edward Island"),
        ("QC", "Quebec"),
        ("SK", "Saskatchewan"),
        ("YT", "Yukon"),
    ]
    
    for code, name in provinces_data:
        # Check if province already exists
        existing = session.query(CanadianProvince).filter(CanadianProvince.code == code).first()
        if not existing:
            province = CanadianProvince(code=code, name=name)
            session.add(province)
            print(f"  ✅ Added {name} ({code})")
        else:
            print(f"  ⏭️  {name} ({code}) already exists")
    
    session.commit()
    print("✅ Canadian provinces seeded successfully")


def seed_admin_user(session):
    """Seed default admin user"""
    print("👤 Seeding admin user...")
    
    admin_email = "admin@maplehustlecan.com"
    admin_password = "Admin123!@#"  # Change this in production
    
    # Check if admin user already exists
    existing_admin = session.query(User).filter(User.email == admin_email).first()
    if existing_admin:
        print(f"  ⏭️  Admin user {admin_email} already exists")
        return existing_admin
    
    # Create admin user
    hashed_password = pwd_context.hash(admin_password)
    admin_user = User(
        email=admin_email,
        hashed_password=hashed_password,
        name="System Administrator",
        role=UserRole.admin,
        status=UserStatus.active,
        is_email_verified=True,
        is_phone_verified=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    session.add(admin_user)
    session.commit()
    session.refresh(admin_user)
    
    print(f"  ✅ Created admin user: {admin_email}")
    print(f"  🔑 Password: {admin_password}")
    print("  ⚠️  Please change the admin password in production!")
    
    return admin_user


def seed_test_users(session):
    """Seed test users for development"""
    print("🧪 Seeding test users...")
    
    test_users = [
        {
            "email": "client@example.com",
            "name": "Test Client",
            "role": UserRole.client,
            "password": "TestClient123!@#"
        },
        {
            "email": "provider@example.com",
            "name": "Test Provider",
            "role": UserRole.provider,
            "password": "TestProvider123!@#"
        },
        {
            "email": "client2@example.com",
            "name": "Another Client",
            "role": UserRole.client,
            "password": "TestClient2123!@#"
        }
    ]
    
    for user_data in test_users:
        # Check if user already exists
        existing = session.query(User).filter(User.email == user_data["email"]).first()
        if existing:
            print(f"  ⏭️  User {user_data['email']} already exists")
            continue
        
        # Create user
        hashed_password = pwd_context.hash(user_data["password"])
        user = User(
            email=user_data["email"],
            hashed_password=hashed_password,
            name=user_data["name"],
            role=user_data["role"],
            status=UserStatus.active,
            is_email_verified=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        session.add(user)
        print(f"  ✅ Created {user_data['role']} user: {user_data['email']}")
    
    session.commit()
    print("✅ Test users seeded successfully")


def seed_notification_preferences(session):
    """Seed default notification preferences for users"""
    print("🔔 Seeding notification preferences...")
    
    # Get all users
    users = session.query(User).all()
    
    for user in users:
        # Check if preferences already exist
        existing = session.execute(
            text("SELECT 1 FROM user_notification_preferences WHERE user_id = :user_id"),
            {"user_id": str(user.id)}
        ).fetchone()
        
        if existing:
            print(f"  ⏭️  Notification preferences for {user.email} already exist")
            continue
        
        # Create default preferences
        session.execute(
            text("""
                INSERT INTO user_notification_preferences (
                    user_id, email_notifications, sms_notifications, 
                    push_notifications, marketing_emails, created_at, updated_at
                ) VALUES (
                    :user_id, true, true, true, false, NOW(), NOW()
                )
            """),
            {"user_id": str(user.id)}
        )
        print(f"  ✅ Created notification preferences for {user.email}")
    
    session.commit()
    print("✅ Notification preferences seeded successfully")


def seed_tax_rules(session):
    """Seed default tax rules for Canadian provinces"""
    print("💰 Seeding tax rules...")
    
    # Canadian tax rates by province (simplified)
    tax_rules = [
        {"province_code": "AB", "rate": 0.05, "name": "GST"},
        {"province_code": "BC", "rate": 0.12, "name": "GST + PST"},
        {"province_code": "MB", "rate": 0.12, "name": "GST + PST"},
        {"province_code": "NB", "rate": 0.15, "name": "HST"},
        {"province_code": "NL", "rate": 0.15, "name": "HST"},
        {"province_code": "NS", "rate": 0.15, "name": "HST"},
        {"province_code": "NT", "rate": 0.05, "name": "GST"},
        {"province_code": "NU", "rate": 0.05, "name": "GST"},
        {"province_code": "ON", "rate": 0.13, "name": "HST"},
        {"province_code": "PE", "rate": 0.15, "name": "HST"},
        {"province_code": "QC", "rate": 0.14975, "name": "GST + QST"},
        {"province_code": "SK", "rate": 0.11, "name": "GST + PST"},
        {"province_code": "YT", "rate": 0.05, "name": "GST"},
    ]
    
    for rule in tax_rules:
        # Check if tax rule already exists
        existing = session.execute(
            text("SELECT 1 FROM tax_rules WHERE province_code = :province_code"),
            {"province_code": rule["province_code"]}
        ).fetchone()
        
        if existing:
            print(f"  ⏭️  Tax rule for {rule['province_code']} already exists")
            continue
        
        # Create tax rule
        session.execute(
            text("""
                INSERT INTO tax_rules (
                    province_code, rate, name, effective_date, created_at, updated_at
                ) VALUES (
                    :province_code, :rate, :name, :effective_date, NOW(), NOW()
                )
            """),
            {
                "province_code": rule["province_code"],
                "rate": rule["rate"],
                "name": rule["name"],
                "effective_date": datetime.utcnow().date()
            }
        )
        print(f"  ✅ Created tax rule for {rule['province_code']}: {rule['name']} ({rule['rate']*100:.2f}%)")
    
    session.commit()
    print("✅ Tax rules seeded successfully")


def main():
    """Run database seeding"""
    print("🌱 Starting database seeding...")
    
    # Create database connection
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        # Run seeding functions
        seed_canadian_provinces(session)
        seed_admin_user(session)
        seed_test_users(session)
        seed_notification_preferences(session)
        seed_tax_rules(session)
        
        print("\n🎉 Database seeding completed successfully!")
        print("\n📋 Summary:")
        print("  ✅ Canadian provinces")
        print("  ✅ Admin user (admin@maplehustlecan.com)")
        print("  ✅ Test users (client, provider)")
        print("  ✅ Notification preferences")
        print("  ✅ Tax rules for all provinces")
        
        print("\n⚠️  Important:")
        print("  - Change admin password in production")
        print("  - Update test user passwords as needed")
        print("  - Review tax rates for accuracy")
        
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        session.rollback()
        sys.exit(1)
    
    finally:
        session.close()


if __name__ == "__main__":
    main()
