"""Add icons to inventory items and remove app URL

Revision ID: 002
Revises: 001
Create Date: 2026-02-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from utils.migration_helpers import add_column_if_not_exists

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add icon column to hardware
    add_column_if_not_exists("hardware", sa.Column("icon", sa.Text, nullable=True))
    
    # Add icon column to vms
    add_column_if_not_exists("vms", sa.Column("icon", sa.Text, nullable=True))
    
    # Add icon column to apps and remove url column
    add_column_if_not_exists("apps", sa.Column("icon", sa.Text, nullable=True))
    op.drop_column("apps", "url")
    
    # Add icon column to storage
    add_column_if_not_exists("storage", sa.Column("icon", sa.Text, nullable=True))
    
    # Add color column to networks
    add_column_if_not_exists("networks", sa.Column("color", sa.Text, nullable=True))
    
    # Add icon column to misc
    add_column_if_not_exists("misc", sa.Column("icon", sa.Text, nullable=True))


def downgrade() -> None:
    # Remove icon from misc
    op.drop_column("misc", "icon")
    
    # Remove color from networks
    op.drop_column("networks", "color")
    
    # Remove icon from storage
    op.drop_column("storage", "icon")
    
    # Add url back to apps and remove icon
    op.add_column("apps", sa.Column("url", sa.Text, nullable=True))
    op.drop_column("apps", "icon")
    
    # Remove icon from vms
    op.drop_column("vms", "icon")
    
    # Remove icon from hardware
    op.drop_column("hardware", "icon")
