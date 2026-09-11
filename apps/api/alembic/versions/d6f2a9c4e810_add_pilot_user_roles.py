"""add minimal single-organization pilot roles"""

from alembic import op
import sqlalchemy as sa


revision = "d6f2a9c4e810"
down_revision = "c8f6a0b4e3d1"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("role", sa.String(30), nullable=True))
    # Existing allowlisted pilot users previously had every application
    # capability. Preserve that effective access; new JIT users start read-only.
    op.execute("UPDATE users SET role = 'administrator' WHERE role IS NULL")
    with op.batch_alter_table("users") as batch:
        batch.alter_column("role", nullable=False, server_default="viewer")
        batch.create_index("ix_users_role", ["role"])


def downgrade():
    with op.batch_alter_table("users") as batch:
        batch.drop_index("ix_users_role")
        batch.drop_column("role")
