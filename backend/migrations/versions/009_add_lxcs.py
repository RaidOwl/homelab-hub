"""add lxcs table and lxc_id to apps and storage"""
from alembic import op
import sqlalchemy as sa

revision = "009_add_lxcs"
down_revision = "008_add_mac_address"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "lxcs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("hardware_id", sa.Integer, sa.ForeignKey("hardware.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("ctid", sa.Integer),
        sa.Column("hostname", sa.Text),
        sa.Column("ip_address", sa.Text),
        sa.Column("mac_address", sa.Text),
        sa.Column("cpu_cores", sa.Integer),
        sa.Column("ram_gb", sa.Float),
        sa.Column("disk_gb", sa.Float),
        sa.Column("os", sa.Text),
        sa.Column("unprivileged", sa.Boolean, server_default="1"),
        sa.Column("onboot", sa.Boolean, server_default="1"),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()),
        if_not_exists=True,
    )




    op.add_column("apps", sa.Column("lxc_id", sa.Integer, nullable=True))
    op.add_column("storage", sa.Column("lxc_id", sa.Integer, nullable=True))


def downgrade():
    op.drop_column("storage", "lxc_id")
    op.drop_column("apps", "lxc_id")
    op.drop_table("lxcs")
