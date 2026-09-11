"""Preserve unknown current relationship activity without changing historical values."""
from alembic import op
import sqlalchemy as sa

revision = "a729e10b3c42"
down_revision = "d6f2a9c4e810"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("business_relationships") as batch:
        batch.alter_column("active", existing_type=sa.Boolean(), nullable=True)


def downgrade():
    # Downgrading must not turn an unknown role into a factual active/inactive role.
    if op.get_bind().scalar(sa.text("SELECT count(*) FROM business_relationships WHERE active IS NULL")):
        raise RuntimeError("Cannot downgrade while relationship activity is unknown")
    with op.batch_alter_table("business_relationships") as batch:
        batch.alter_column("active", existing_type=sa.Boolean(), nullable=False)
