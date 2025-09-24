"""add seed data migration for provinces, roles, and admin user"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from datetime import datetime
from passlib.context import CryptContext

# revision identifiers
revision = "add_seed_data_migration"
down_revision = "add_missing_cascade_constraints"
branch_labels = None
depends_on = None

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def upgrade():
    """Add seed data for provinces, roles, and admin user"""
    
    # Insert Canadian provinces
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
        op.execute(
            text("""
                INSERT INTO canadian_provinces (code, name, created_at, updated_at)
                VALUES (:code, :name, NOW(), NOW())
                ON CONFLICT (code) DO NOTHING
            """),
            {"code": code, "name": name}
        )
    
    # Insert default admin user
    admin_email = "admin@maplehustlecan.com"
    admin_password = "Admin123!@#"  # Change this in production
    hashed_password = pwd_context.hash(admin_password)
    
    op.execute(
        text("""
            INSERT INTO users (
                id, email, hashed_password, name, role, status, 
                is_email_verified, is_phone_verified, created_at, updated_at
            )
            VALUES (
                gen_random_uuid(), :email, :password, :name, :role, :status,
                true, true, NOW(), NOW()
            )
            ON CONFLICT (email) DO NOTHING
        """),
        {
            "email": admin_email,
            "password": hashed_password,
            "name": "System Administrator",
            "role": "admin",
            "status": "active"
        }
    )
    
    # Insert test users
    test_users = [
        {
            "email": "client@example.com",
            "name": "Test Client",
            "role": "client",
            "password": pwd_context.hash("TestClient123!@#")
        },
        {
            "email": "provider@example.com",
            "name": "Test Provider",
            "role": "provider",
            "password": pwd_context.hash("TestProvider123!@#")
        }
    ]
    
    for user in test_users:
        op.execute(
            text("""
                INSERT INTO users (
                    id, email, hashed_password, name, role, status,
                    is_email_verified, created_at, updated_at
                )
                VALUES (
                    gen_random_uuid(), :email, :password, :name, :role, :status,
                    true, NOW(), NOW()
                )
                ON CONFLICT (email) DO NOTHING
            """),
            {
                "email": user["email"],
                "password": user["password"],
                "name": user["name"],
                "role": user["role"],
                "status": "active"
            }
        )
    
    # Insert tax rules for Canadian provinces
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
        op.execute(
            text("""
                INSERT INTO tax_rules (
                    province_code, rate, name, effective_date, created_at, updated_at
                )
                VALUES (
                    :province_code, :rate, :name, :effective_date, NOW(), NOW()
                )
                ON CONFLICT (province_code) DO NOTHING
            """),
            {
                "province_code": rule["province_code"],
                "rate": rule["rate"],
                "name": rule["name"],
                "effective_date": datetime.utcnow().date()
            }
        )
    
    # Insert default notification preferences for all users
    op.execute(
        text("""
            INSERT INTO user_notification_preferences (
                user_id, email_notifications, sms_notifications, 
                push_notifications, marketing_emails, created_at, updated_at
            )
            SELECT 
                u.id, true, true, true, false, NOW(), NOW()
            FROM users u
            WHERE NOT EXISTS (
                SELECT 1 FROM user_notification_preferences unp 
                WHERE unp.user_id = u.id
            )
        """)
    )


def downgrade():
    """Remove seed data"""
    # Remove notification preferences
    op.execute(text("DELETE FROM user_notification_preferences"))
    
    # Remove tax rules
    op.execute(text("DELETE FROM tax_rules"))
    
    # Remove test users (keep admin for safety)
    op.execute(text("DELETE FROM users WHERE email IN ('client@example.com', 'provider@example.com')"))
    
    # Note: We don't remove provinces or admin user in downgrade for safety
