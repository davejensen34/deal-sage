"""add human analyst case conclusions"""

from alembic import op
import sqlalchemy as sa

revision = "f39a02bd7c41"
down_revision = "e28c91a4b6d0"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "analyst_conclusions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_id", sa.Integer(), sa.ForeignKey("research_cases.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("analyst_name", sa.String(160), nullable=False),
        sa.Column("outcome", sa.String(60), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("supporting_inference_ids", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ("case_id", "user_id", "outcome", "status"):
        op.create_index(f"ix_analyst_conclusions_{column}", "analyst_conclusions", [column])


def downgrade():
    op.drop_table("analyst_conclusions")
