"""Add Proxmox node and cluster entities

Revision ID: 009_add_proxmox_entities
Revises: 008_add_mac_address
Create Date: 2026-03-04

"""
from alembic import op
import sqlalchemy as sa
from utils.migration_helpers import add_column_if_not_exists


# revision identifiers, used by Alembic.
revision = '009_add_proxmox_entities'
down_revision = '008_add_mac_address'
branch_labels = None
depends_on = None


def upgrade():
    # Create clusters table
    op.create_table(
        'clusters',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create nodes table
    op.create_table(
        'nodes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('hostname', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.Text(), nullable=True),
        sa.Column('mac_address', sa.Text(), nullable=True),
        sa.Column('cpu', sa.Text(), nullable=True),
        sa.Column('cpu_cores', sa.Integer(), nullable=True),
        sa.Column('ram_gb', sa.Float(), nullable=True),
        sa.Column('os', sa.Text(), nullable=True),
        sa.Column('cluster_id', sa.Integer(), nullable=True),
        sa.Column('icon', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['cluster_id'], ['clusters.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Add node_id to vms (and make hardware_id nullable)
    add_column_if_not_exists('vms', sa.Column('node_id', sa.Integer(), nullable=True))
    add_column_if_not_exists('vms', sa.Column('vm_type', sa.Text(), nullable=True))

    # Add node_id to apps
    add_column_if_not_exists('apps', sa.Column('node_id', sa.Integer(), nullable=True))

    # Add node_id to storage
    add_column_if_not_exists('storage', sa.Column('node_id', sa.Integer(), nullable=True))


def downgrade():
    op.drop_column('storage', 'node_id')
    op.drop_column('apps', 'node_id')
    op.drop_column('vms', 'vm_type')
    op.drop_column('vms', 'node_id')
    op.drop_table('nodes')
    op.drop_table('clusters')
