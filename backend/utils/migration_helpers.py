from alembic import op
from sqlalchemy.exc import OperationalError

def add_column_if_not_exists(table_name, column):
    """Add a column only if it doesn't already exist."""
    try:
        op.add_column(table_name,column)
    except OperationalError:
        # Column already exists, skip
        pass

