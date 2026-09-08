"""add immutable analyst dispositions for model proposals"""

from alembic import op
import sqlalchemy as sa


revision = "c3fa5b7d62e8"
down_revision = "b2e94a8c51d7"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "model_proposal_dispositions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("proposal_id", sa.Integer(), sa.ForeignKey("model_proposals.id"), nullable=False),
        sa.Column("case_id", sa.Integer(), sa.ForeignKey("research_cases.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("analyst_name", sa.String(160), nullable=False),
        sa.Column("decision", sa.String(30), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("corrected_output", sa.JSON(), nullable=True),
        sa.Column("supporting_evidence_ids", sa.JSON(), nullable=False),
        sa.Column("supporting_claim_ids", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ("proposal_id", "case_id", "user_id", "decision"):
        op.create_index(
            f"ix_model_proposal_dispositions_{column}",
            "model_proposal_dispositions",
            [column],
        )


def downgrade():
    op.drop_table("model_proposal_dispositions")
