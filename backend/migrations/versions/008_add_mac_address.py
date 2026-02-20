"""add mac address to hardware and vms

Revision ID: 008_add_mac_address
Revises: add89462ccd0
Create Date: 2026-02-18

"""
from alembic import op
import sqlalchemy as sa
from utils.migration_helpers import add_column_if_not_exists


# revision identifiers, used by Alembic.
revision = '008_add_mac_address'
down_revision = 'add89462ccd0'
branch_labels = None
depends_on = None


def upgrade():
    # Add mac_address column to hardware table
    add_column_if_not_exists('hardware', sa.Column('mac_address', sa.Text(), nullable=True))
    
    # Add mac_address column to vms table
    add_column_if_not_exists('vms', sa.Column('mac_address', sa.Text(), nullable=True))


def downgrade():
    # Remove mac_address column from vms table
    op.drop_column('vms', 'mac_address')
    
    # Remove mac_address column from hardware table
    op.drop_column('hardware', 'mac_address')
