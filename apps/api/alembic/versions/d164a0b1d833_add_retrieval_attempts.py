"""Retain bounded document authorizations before external I/O."""
from alembic import op
import sqlalchemy as sa

revision = "d164a0b1d833"
down_revision = "c158a0b1d832"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("retrieval_attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("request_key", sa.String(36), nullable=False, unique=True),
        sa.Column("case_id", sa.Integer(), sa.ForeignKey("research_cases.id"), nullable=False),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("source_candidates.id"), nullable=False),
        sa.Column("actor", sa.String(160), nullable=False),
        sa.Column("plan", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("recovery_after", sa.DateTime(timezone=True), nullable=False),
        sa.Column("evidence_id", sa.Integer(), sa.ForeignKey("case_evidence.id")),
        sa.Column("error_code", sa.String(60)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_retrieval_attempts_case_id", "retrieval_attempts", ["case_id"])
    op.create_index("ix_retrieval_attempts_source_id", "retrieval_attempts", ["source_id"])


def downgrade():
    if op.get_bind().execute(sa.text("SELECT COUNT(*) FROM retrieval_attempts")).scalar():
        raise RuntimeError("Cannot discard retained retrieval attempts")
    op.drop_table("retrieval_attempts")
