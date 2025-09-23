"""fix availability schema (replace TSRANGE with date+time fields)"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# --- Alembic revision identifiers ---
revision = "b65c82ba4740"
down_revision = "xxxx_add_canadian_provinces"
branch_labels = None
depends_on = None


def upgrade():
    # 1. Add new columns
    op.add_column("availability", sa.Column("date", sa.Date(), nullable=True))
    op.add_column("availability", sa.Column("start_time", sa.Time(), nullable=True))
    op.add_column("availability", sa.Column("end_time", sa.Time(), nullable=True))

    # 2. Optional: migrate existing data from TSRANGE into new fields
    # (only if you already had production data!)
    # For now, we'll skip data migration, since TSRANGE isn't accessible without custom SQL.

    # 3. Drop the old TSRANGE column
    op.drop_column("availability", "daterange")

    # 4. Make new columns non-nullable
    op.alter_column("availability", "date", nullable=False)
    op.alter_column("availability", "start_time", nullable=False)
    op.alter_column("availability", "end_time", nullable=False)


def downgrade():
    # 1. Add back the old daterange column
    op.add_column("availability", sa.Column("daterange", postgresql.TSRANGE(), nullable=False))

    # 2. Drop new columns
    op.drop_column("availability", "end_time")
    op.drop_column("availability", "start_time")
    op.drop_column("availability", "date")
