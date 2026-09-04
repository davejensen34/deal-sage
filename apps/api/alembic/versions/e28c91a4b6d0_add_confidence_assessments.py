"""add explainable confidence and profile observations"""

from alembic import op
import sqlalchemy as sa

revision = "e28c91a4b6d0"
down_revision = "d17b8e4a9031"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "confidence_assessments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_id", sa.Integer(), sa.ForeignKey("research_cases.id"), nullable=False),
        sa.Column("method_version", sa.String(60), nullable=False),
        sa.Column("business_identity", sa.Integer(), nullable=False),
        sa.Column("owner_relationship", sa.Integer(), nullable=False),
        sa.Column("transition_identity", sa.Integer(), nullable=False),
        sa.Column("operating_status", sa.Integer(), nullable=False),
        sa.Column("overall_opportunity", sa.Integer(), nullable=False),
        sa.Column("factors", sa.JSON(), nullable=False),
        sa.Column("supporting_claim_ids", sa.JSON(), nullable=False),
        sa.Column("contradictory_claim_ids", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_confidence_assessments_case_id", "confidence_assessments", ["case_id"])
    op.create_index("ix_confidence_assessments_method_version", "confidence_assessments", ["method_version"])
    op.create_table(
        "business_profile_observations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_id", sa.Integer(), sa.ForeignKey("research_cases.id"), nullable=False),
        sa.Column("field_name", sa.String(80), nullable=False),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column("classification", sa.String(40), nullable=False),
        sa.Column("supporting_claim_ids", sa.JSON(), nullable=False),
        sa.Column("inference_id", sa.Integer(), sa.ForeignKey("research_inferences.id")),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ("case_id", "field_name", "classification", "inference_id"):
        op.create_index(
            f"ix_business_profile_observations_{column}",
            "business_profile_observations",
            [column],
        )


def downgrade():
    op.drop_table("business_profile_observations")
    op.drop_table("confidence_assessments")
