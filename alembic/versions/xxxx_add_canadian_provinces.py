"""add canadian provinces reference table"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "xxxx_add_canadian_provinces"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "canadian_provinces",
        sa.Column("code", sa.String(length=2), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
    )

    # --- Seed Canadian Provinces ---
    provinces = [
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

    conn = op.get_bind()
    for code, name in provinces:
        conn.execute(
            sa.text("INSERT INTO canadian_provinces (code, name) VALUES (:code, :name)"),
            {"code": code, "name": name},
        )


def downgrade():
    op.drop_table("canadian_provinces")
