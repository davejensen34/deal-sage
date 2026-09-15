"""Durable one-packet model authorizations."""
from alembic import op
import sqlalchemy as sa

revision = "e168a0b1d834"
down_revision = "d164a0b1d833"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("extraction_attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("request_key", sa.String(36), nullable=False, unique=True),
        sa.Column("case_id", sa.Integer(), sa.ForeignKey("research_cases.id"), nullable=False),
        sa.Column("evidence_id", sa.Integer(), sa.ForeignKey("case_evidence.id"), nullable=False),
        sa.Column("actor", sa.String(160), nullable=False),
        sa.Column("actor_key", sa.String(100), nullable=False),
        sa.Column("plan", sa.JSON(), nullable=False),
        sa.Column("plan_hash", sa.String(64), nullable=False),
        sa.Column("reserved_cents", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("recovery_after", sa.DateTime(timezone=True), nullable=False),
        sa.Column("proposal_id", sa.Integer(), sa.ForeignKey("model_proposals.id")),
        sa.Column("error_code", sa.String(60)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_extraction_attempts_case_id", "extraction_attempts", ["case_id"])


def downgrade():
    if op.get_bind().execute(sa.text("SELECT COUNT(*) FROM extraction_attempts")).scalar():
        raise RuntimeError("Cannot discard retained extraction attempts")
    op.drop_table("extraction_attempts")
