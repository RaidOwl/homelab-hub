"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-02-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from utils.migration_helpers import add_column_if_not_exists

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "hardware",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        if_not_exists=True,
    )
    # Add columns individually to handle existing tables with incomplete schemas
    add_column_if_not_exists("hardware", sa.Column("name", sa.Text, nullable=False, server_default=""))
    add_column_if_not_exists("hardware", sa.Column("hostname", sa.Text))
    add_column_if_not_exists("hardware", sa.Column("ip_address", sa.Text))
    add_column_if_not_exists("hardware", sa.Column("cpu", sa.Text))
    add_column_if_not_exists("hardware", sa.Column("cpu_cores", sa.Integer))
    add_column_if_not_exists("hardware", sa.Column("ram_gb", sa.Float))
    add_column_if_not_exists("hardware", sa.Column("os", sa.Text))
    add_column_if_not_exists("hardware", sa.Column("make", sa.Text))
    add_column_if_not_exists("hardware", sa.Column("model", sa.Text))
    add_column_if_not_exists("hardware", sa.Column("serial_number", sa.Text))
    add_column_if_not_exists("hardware", sa.Column("location", sa.Text))
    add_column_if_not_exists("hardware", sa.Column("notes", sa.Text))
    add_column_if_not_exists("hardware", sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()))
    add_column_if_not_exists("hardware", sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()))

    op.create_table(
        "vms",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        if_not_exists=True,
    )
    add_column_if_not_exists("vms", sa.Column("hardware_id", sa.Integer, sa.ForeignKey("hardware.id", ondelete="CASCADE"), nullable=False, server_default="0"))
    add_column_if_not_exists("vms", sa.Column("name", sa.Text, nullable=False, server_default=""))
    add_column_if_not_exists("vms", sa.Column("hostname", sa.Text))
    add_column_if_not_exists("vms", sa.Column("ip_address", sa.Text))
    add_column_if_not_exists("vms", sa.Column("cpu_cores", sa.Integer))
    add_column_if_not_exists("vms", sa.Column("ram_gb", sa.Float))
    add_column_if_not_exists("vms", sa.Column("disk_gb", sa.Float))
    add_column_if_not_exists("vms", sa.Column("os", sa.Text))
    add_column_if_not_exists("vms", sa.Column("hypervisor", sa.Text))
    add_column_if_not_exists("vms", sa.Column("notes", sa.Text))
    add_column_if_not_exists("vms", sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()))
    add_column_if_not_exists("vms", sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()))

    op.create_table(
        "apps",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        if_not_exists=True,
    )
    add_column_if_not_exists("apps", sa.Column("hardware_id", sa.Integer, sa.ForeignKey("hardware.id", ondelete="SET NULL"), nullable=True))
    add_column_if_not_exists("apps", sa.Column("vm_id", sa.Integer, sa.ForeignKey("vms.id", ondelete="SET NULL"), nullable=True))
    add_column_if_not_exists("apps", sa.Column("name", sa.Text, nullable=False, server_default=""))
    add_column_if_not_exists("apps", sa.Column("description", sa.Text))
    add_column_if_not_exists("apps", sa.Column("hostname", sa.Text))
    add_column_if_not_exists("apps", sa.Column("external_hostname", sa.Text))
    add_column_if_not_exists("apps", sa.Column("port", sa.Integer))
    add_column_if_not_exists("apps", sa.Column("url", sa.Text))
    add_column_if_not_exists("apps", sa.Column("notes", sa.Text))
    add_column_if_not_exists("apps", sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()))
    add_column_if_not_exists("apps", sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()))

    op.create_table(
        "storage",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        if_not_exists=True,
    )
    add_column_if_not_exists("storage", sa.Column("hardware_id", sa.Integer, sa.ForeignKey("hardware.id", ondelete="SET NULL"), nullable=True))
    add_column_if_not_exists("storage", sa.Column("vm_id", sa.Integer, sa.ForeignKey("vms.id", ondelete="SET NULL"), nullable=True))
    add_column_if_not_exists("storage", sa.Column("name", sa.Text, nullable=False, server_default=""))
    add_column_if_not_exists("storage", sa.Column("storage_type", sa.Text))
    add_column_if_not_exists("storage", sa.Column("raid_type", sa.Text))
    add_column_if_not_exists("storage", sa.Column("drive_count", sa.Integer))
    add_column_if_not_exists("storage", sa.Column("raw_space_gb", sa.Float))
    add_column_if_not_exists("storage", sa.Column("usable_space_gb", sa.Float))
    add_column_if_not_exists("storage", sa.Column("filesystem", sa.Text))
    add_column_if_not_exists("storage", sa.Column("notes", sa.Text))
    add_column_if_not_exists("storage", sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()))
    add_column_if_not_exists("storage", sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()))

    op.create_table(
        "networks",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        if_not_exists=True,
    )
    add_column_if_not_exists("networks", sa.Column("name", sa.Text, nullable=False, server_default=""))
    add_column_if_not_exists("networks", sa.Column("vlan_id", sa.Integer))
    add_column_if_not_exists("networks", sa.Column("subnet", sa.Text))
    add_column_if_not_exists("networks", sa.Column("gateway", sa.Text))
    add_column_if_not_exists("networks", sa.Column("dns_servers", sa.Text))
    add_column_if_not_exists("networks", sa.Column("notes", sa.Text))
    add_column_if_not_exists("networks", sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()))
    add_column_if_not_exists("networks", sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()))

    op.create_table(
        "network_members",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        if_not_exists=True,
    )
    add_column_if_not_exists("network_members", sa.Column("network_id", sa.Integer, sa.ForeignKey("networks.id", ondelete="CASCADE"), nullable=False, server_default="0"))
    add_column_if_not_exists("network_members", sa.Column("member_type", sa.Text, nullable=False, server_default=""))
    add_column_if_not_exists("network_members", sa.Column("member_id", sa.Integer, nullable=False, server_default="0"))
    add_column_if_not_exists("network_members", sa.Column("ip_on_network", sa.Text))
    add_column_if_not_exists("network_members", sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()))
    add_column_if_not_exists("network_members", sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()))

    op.create_table(
        "misc",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        if_not_exists=True,
    )
    add_column_if_not_exists("misc", sa.Column("name", sa.Text, nullable=False, server_default=""))
    add_column_if_not_exists("misc", sa.Column("category", sa.Text))
    add_column_if_not_exists("misc", sa.Column("description", sa.Text))
    add_column_if_not_exists("misc", sa.Column("properties", sa.Text))
    add_column_if_not_exists("misc", sa.Column("notes", sa.Text))
    add_column_if_not_exists("misc", sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()))
    add_column_if_not_exists("misc", sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()))

    op.create_table(
        "documents",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        if_not_exists=True,
    )
    add_column_if_not_exists("documents", sa.Column("parent_id", sa.Integer, sa.ForeignKey("documents.id", ondelete="SET NULL"), nullable=True))
    add_column_if_not_exists("documents", sa.Column("title", sa.Text, nullable=False, server_default="Untitled"))
    add_column_if_not_exists("documents", sa.Column("content", sa.Text, nullable=False, server_default=""))
    add_column_if_not_exists("documents", sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"))
    add_column_if_not_exists("documents", sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()))
    add_column_if_not_exists("documents", sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()))

    op.create_table(
        "map_layout",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        if_not_exists=True,
    )
    add_column_if_not_exists("map_layout", sa.Column("node_type", sa.Text, nullable=False, server_default=""))
    add_column_if_not_exists("map_layout", sa.Column("node_id", sa.Integer, nullable=False, server_default="0"))
    add_column_if_not_exists("map_layout", sa.Column("x", sa.Float, nullable=False, server_default="0"))
    add_column_if_not_exists("map_layout", sa.Column("y", sa.Float, nullable=False, server_default="0"))
    add_column_if_not_exists("map_layout", sa.Column("pinned", sa.Boolean, nullable=False, server_default="0"))

    op.create_table(
        "map_edges",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        if_not_exists=True,
    )
    add_column_if_not_exists("map_edges", sa.Column("source_type", sa.Text, nullable=False, server_default=""))
    add_column_if_not_exists("map_edges", sa.Column("source_id", sa.Integer, nullable=False, server_default="0"))
    add_column_if_not_exists("map_edges", sa.Column("target_type", sa.Text, nullable=False, server_default=""))
    add_column_if_not_exists("map_edges", sa.Column("target_id", sa.Integer, nullable=False, server_default="0"))
    add_column_if_not_exists("map_edges", sa.Column("label", sa.Text))
    add_column_if_not_exists("map_edges", sa.Column("style", sa.Text))

    op.create_table(
        "relationships",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        if_not_exists=True,
    )
    add_column_if_not_exists("relationships", sa.Column("source_type", sa.Text, nullable=False, server_default=""))
    add_column_if_not_exists("relationships", sa.Column("source_id", sa.Integer, nullable=False, server_default="0"))
    add_column_if_not_exists("relationships", sa.Column("target_type", sa.Text, nullable=False, server_default=""))
    add_column_if_not_exists("relationships", sa.Column("target_id", sa.Integer, nullable=False, server_default="0"))
    add_column_if_not_exists("relationships", sa.Column("label", sa.Text))


def downgrade() -> None:
    op.drop_table("relationships")
    op.drop_table("map_edges")
    op.drop_table("map_layout")
    op.drop_table("documents")
    op.drop_table("misc")
    op.drop_table("network_members")
    op.drop_table("networks")
    op.drop_table("storage")
    op.drop_table("apps")
    op.drop_table("vms")
    op.drop_table("hardware")
