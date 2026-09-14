"""Add opt-in frozen signal intake policy; preserve historical cases."""

from alembic import op
import sqlalchemy as sa

revision = "b144f0a9c721"
down_revision = "a729e10b3c42"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("research_cases", sa.Column("signal_intake_policy", sa.JSON(none_as_null=True), nullable=True))


def downgrade():
    # Dropping a configured policy would silently remove its paid-analysis gate.
    if op.get_bind().execute(sa.text("SELECT COUNT(*) FROM research_cases WHERE signal_intake_policy IS NOT NULL")).scalar():
        raise RuntimeError("Cannot remove configured signal intake policies")
    with op.batch_alter_table("research_cases") as batch:
        batch.drop_column("signal_intake_policy")
