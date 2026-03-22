"""add hardware_type to hardware

Revision ID: 009_add_hardware_type
Revises: 008_add_mac_address
Create Date: 2026-03-22

"""
from alembic import op
import sqlalchemy as sa
from utils.migration_helpers import add_column_if_not_exists


# revision identifiers, used by Alembic.
revision = '009_add_hardware_type'
down_revision = '008_add_mac_address'
branch_labels = None
depends_on = None


def upgrade():
    add_column_if_not_exists('hardware', sa.Column('hardware_type', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('hardware', 'hardware_type')
