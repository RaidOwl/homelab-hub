"""add linked entity fields to documents

Revision ID: 009_add_document_links
Revises: 008_add_mac_address
Create Date: 2026-02-28

"""
from alembic import op
import sqlalchemy as sa
from utils.migration_helpers import add_column_if_not_exists


# revision identifiers, used by Alembic.
revision = '009_add_document_links'
down_revision = '008_add_mac_address'
branch_labels = None
depends_on = None


def upgrade():
    # Add linked_entity_type column to documents table
    add_column_if_not_exists('documents', sa.Column('linked_entity_type', sa.Text(), nullable=True))
    
    # Add linked_entity_id column to documents table
    add_column_if_not_exists('documents', sa.Column('linked_entity_id', sa.Integer(), nullable=True))


def downgrade():
    # Remove linked entity columns from documents table
    op.drop_column('documents', 'linked_entity_id')
    op.drop_column('documents', 'linked_entity_type')
