"""add evidence-bounded model proposals"""

from alembic import op
import sqlalchemy as sa


revision = "d84a0c4e219f"
down_revision = "c61d9b270a55"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "model_proposals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_id", sa.Integer(), sa.ForeignKey("research_cases.id"), nullable=False),
        sa.Column("task", sa.String(40), nullable=False),
        sa.Column("provider", sa.String(60), nullable=False),
        sa.Column("model", sa.String(120), nullable=False),
        sa.Column("prompt_version", sa.String(80), nullable=False),
        sa.Column("schema_version", sa.String(80), nullable=False),
        sa.Column("execution_outcome", sa.String(30), nullable=False),
        sa.Column("proposed_output", sa.JSON()),
        sa.Column("supported_evidence_ids", sa.JSON(), nullable=False),
        sa.Column("supported_claim_ids", sa.JSON(), nullable=False),
        sa.Column("input_tokens", sa.Integer()),
        sa.Column("output_tokens", sa.Integer()),
        sa.Column("total_tokens", sa.Integer()),
        sa.Column("latency_ms", sa.Integer()),
        sa.Column("cost_cents", sa.Integer(), nullable=False),
        sa.Column("error_class", sa.String(120)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ("case_id", "task", "provider", "execution_outcome"):
        op.create_index(f"ix_model_proposals_{column}", "model_proposals", [column])


def downgrade():
    op.drop_table("model_proposals")
