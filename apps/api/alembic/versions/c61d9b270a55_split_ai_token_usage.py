"""split AI execution input and output token usage"""

from alembic import op
import sqlalchemy as sa


revision = "c61d9b270a55"
down_revision = "f39a02bd7c41"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("ai_executions") as batch:
        batch.add_column(sa.Column("input_tokens", sa.Integer()))
        batch.add_column(sa.Column("output_tokens", sa.Integer()))


def downgrade():
    with op.batch_alter_table("ai_executions") as batch:
        batch.drop_column("output_tokens")
        batch.drop_column("input_tokens")
