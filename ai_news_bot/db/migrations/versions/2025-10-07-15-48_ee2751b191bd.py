"""Change constrains.

Revision ID: ee2751b191bd
Revises: 09c9c13cb1bd
Create Date: 2025-10-07 15:48:44.770025

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "ee2751b191bd"
down_revision = "09c9c13cb1bd"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Run the migration."""
    # Create new table with correct constraints
    op.create_table(
        "tg_user_new",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tg_id", sa.Integer(), nullable=False),
        sa.Column("tg_chat_id", sa.Integer(), nullable=False), 
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tg_id", "tg_chat_id", name="uq_tg_user_tg_id_tg_chat_id"),
    )
    
    # Copy data from old table
    op.execute("INSERT INTO tg_user_new (id, tg_id, tg_chat_id, created_at) SELECT id, tg_id, tg_chat_id, created_at FROM tg_user")
    
    # Drop old table and rename new one
    op.drop_table("tg_user")
    op.rename_table("tg_user_new", "tg_user")


def downgrade() -> None:
    """Undo the migration."""
    # Recreate original table structure
    op.create_table(
        "tg_user_old",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tg_id", sa.Integer(), nullable=False),
        sa.Column("tg_chat_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tg_chat_id"),
        sa.UniqueConstraint("tg_id"),
    )
    
    # Copy data back
    op.execute("INSERT INTO tg_user_old (id, tg_id, tg_chat_id, created_at) SELECT id, tg_id, tg_chat_id, created_at FROM tg_user")
    
    # Replace table
    op.drop_table("tg_user")
    op.rename_table("tg_user_old", "tg_user")