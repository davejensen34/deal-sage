"""add reproducible candidate score assessments"""

from alembic import op
import sqlalchemy as sa

revision = "f5c1d2e3a4b5"
down_revision = "c3fa5b7d62e8"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "candidate_score_assessments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("candidate_id", sa.Integer(), sa.ForeignKey("candidate_matches.id"), nullable=False),
        sa.Column("method_version", sa.String(60), nullable=False),
        sa.Column("provenance_classification", sa.String(40), nullable=False),
        sa.Column("owner_business_confidence", sa.Integer(), nullable=False),
        sa.Column("signal_identity_confidence", sa.Integer(), nullable=False),
        sa.Column("contradiction_penalty", sa.Integer(), nullable=False),
        sa.Column("overall_candidate_confidence", sa.Integer(), nullable=False),
        sa.Column("factors", sa.JSON(), nullable=False),
        sa.Column("supporting_evidence_ids", sa.JSON(), nullable=False),
        sa.Column("calculation", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ("candidate_id", "method_version", "provenance_classification"):
        op.create_index(f"ix_candidate_score_assessments_{column}", "candidate_score_assessments", [column])


def downgrade():
    op.drop_table("candidate_score_assessments")
