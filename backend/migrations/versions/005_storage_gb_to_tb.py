"""Change storage space from GB to TB

Revision ID: 005
Revises: 004
Create Date: 2026-02-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from utils.migration_helpers import add_column_if_not_exists

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SQLite doesn't support column rename directly, so we need to:
    # 1. Add new columns
    # 2. Copy data (converting GB to TB)
    # 3. Drop old columns
    
    # Add new TB columns
    add_column_if_not_exists("storage", sa.Column("raw_space_tb", sa.Float, nullable=True))
    add_column_if_not_exists("storage", sa.Column("usable_space_tb", sa.Float, nullable=True))
    
    # Convert GB to TB (divide by 1024)
    op.execute("""
        UPDATE storage 
        SET raw_space_tb = raw_space_gb / 1024.0
        WHERE raw_space_gb IS NOT NULL
    """)
    op.execute("""
        UPDATE storage 
        SET usable_space_tb = usable_space_gb / 1024.0
        WHERE usable_space_gb IS NOT NULL
    """)
    
    # Drop old GB columns
    op.drop_column("storage", "raw_space_gb")
    op.drop_column("storage", "usable_space_gb")


def downgrade() -> None:
    # Add back GB columns
    add_column_if_not_exists("storage", sa.Column("raw_space_gb", sa.Float, nullable=True))
    add_column_if_not_exists("storage", sa.Column("usable_space_gb", sa.Float, nullable=True))
    
    # Convert TB back to GB (multiply by 1024)
    op.execute("""
        UPDATE storage 
        SET raw_space_gb = raw_space_tb * 1024.0
        WHERE raw_space_tb IS NOT NULL
    """)
    op.execute("""
        UPDATE storage 
        SET usable_space_gb = usable_space_tb * 1024.0
        WHERE usable_space_tb IS NOT NULL
    """)
    
    # Drop TB columns
    op.drop_column("storage", "raw_space_tb")
    op.drop_column("storage", "usable_space_tb")
