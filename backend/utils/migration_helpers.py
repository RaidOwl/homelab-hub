from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text


def add_column_if_not_exists(table_name, column):
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [c['name'] for c in inspector.get_columns(table_name)]
    if column.name not in columns:
        op.add_column(table_name, column)


def drop_column_if_exists(table_name, column_name):
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [c['name'] for c in inspector.get_columns(table_name)]
    if column_name in columns:
        op.drop_column(table_name, column_name)
