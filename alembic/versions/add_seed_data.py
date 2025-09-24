"""add seed data for provinces, roles, and initial admin user"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text
from passlib.context import CryptContext

# revision identifiers
revision = "add_seed_data"
down_revision = "add_indexes_and_constraints"
branch_labels = None
depends_on = None

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def upgrade():
    conn = op.get_bind()
    
    # Insert Canadian provinces (if not already exists)
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
        conn.execute(
            text("""
                INSERT INTO canadian_provinces (code, name) 
                VALUES (:code, :name) 
                ON CONFLICT (code) DO NOTHING
            """),
            {"code": code, "name": name}
        )
    
    # Create default admin user (if not exists)
    admin_email = "admin@maplehustlecan.com"
    admin_password = pwd_context.hash("admin123!")  # Change this in production
    
    conn.execute(
        text("""
            INSERT INTO users (
                id, email, hashed_password, name, role, status, 
                is_email_verified, created_at, updated_at
            ) VALUES (
                gen_random_uuid(), :email, :password, :name, :role, :status,
                true, NOW(), NOW()
            ) ON CONFLICT (email) DO NOTHING
        """),
        {
            "email": admin_email,
            "password": admin_password,
            "name": "System Administrator",
            "role": "admin",
            "status": "active"
        }
    )
    
    # Insert default notification preferences for admin
    conn.execute(
        text("""
            INSERT INTO user_notification_preferences (
                user_id, email_notifications, sms_notifications, 
                push_notifications, marketing_emails, created_at, updated_at
            ) 
            SELECT u.id, true, true, true, false, NOW(), NOW()
            FROM users u 
            WHERE u.email = :email
            ON CONFLICT (user_id) DO NOTHING
        """),
        {"email": admin_email}
    )


def downgrade():
    conn = op.get_bind()
    
    # Remove admin user
    conn.execute(
        text("DELETE FROM users WHERE email = :email"),
        {"email": "admin@maplehustlecan.com"}
    )
    
    # Remove provinces (optional - you might want to keep them)
    # conn.execute(text("DELETE FROM canadian_provinces"))
