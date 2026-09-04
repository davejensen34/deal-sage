"""add bidirectional identity resolution provenance"""

from alembic import op
import sqlalchemy as sa


revision = "d17b8e4a9031"
down_revision = "c95f5c279e02"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "case_aliases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_id", sa.Integer(), sa.ForeignKey("research_cases.id"), nullable=False),
        sa.Column("entity_type", sa.String(30), nullable=False),
        sa.Column("canonical_value", sa.String(240), nullable=False),
        sa.Column("alias_value", sa.String(240), nullable=False),
        sa.Column("normalized_value", sa.String(240), nullable=False),
        sa.Column(
            "source_claim_id",
            sa.Integer(),
            sa.ForeignKey("evidence_claims.id"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "case_id", "entity_type", "normalized_value", name="uq_case_alias_normalized"
        ),
    )
    for column in ("case_id", "entity_type", "normalized_value", "source_claim_id"):
        op.create_index(f"ix_case_aliases_{column}", "case_aliases", [column])
    op.create_table(
        "claim_contradictions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_id", sa.Integer(), sa.ForeignKey("research_cases.id"), nullable=False),
        sa.Column("left_claim_id", sa.Integer(), sa.ForeignKey("evidence_claims.id"), nullable=False),
        sa.Column("right_claim_id", sa.Integer(), sa.ForeignKey("evidence_claims.id"), nullable=False),
        sa.Column("contradiction_type", sa.String(60), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "case_id", "left_claim_id", "right_claim_id", name="uq_case_claim_conflict"
        ),
    )
    for column in (
        "case_id",
        "left_claim_id",
        "right_claim_id",
        "contradiction_type",
        "status",
    ):
        op.create_index(
            f"ix_claim_contradictions_{column}", "claim_contradictions", [column]
        )
    op.create_table(
        "evidence_relationships",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_id", sa.Integer(), sa.ForeignKey("research_cases.id"), nullable=False),
        sa.Column("left_evidence_id", sa.Integer(), sa.ForeignKey("case_evidence.id"), nullable=False),
        sa.Column("right_evidence_id", sa.Integer(), sa.ForeignKey("case_evidence.id"), nullable=False),
        sa.Column("relationship_type", sa.String(40), nullable=False),
        sa.Column("basis", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "case_id", "left_evidence_id", "right_evidence_id", name="uq_case_evidence_pair"
        ),
    )
    for column in (
        "case_id",
        "left_evidence_id",
        "right_evidence_id",
        "relationship_type",
    ):
        op.create_index(
            f"ix_evidence_relationships_{column}", "evidence_relationships", [column]
        )
    op.create_table(
        "identity_resolutions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_id", sa.Integer(), sa.ForeignKey("research_cases.id"), nullable=False),
        sa.Column("direction", sa.String(40), nullable=False),
        sa.Column("subject_value", sa.String(240), nullable=False),
        sa.Column("candidate_value", sa.String(240), nullable=False),
        sa.Column("supporting_claim_ids", sa.JSON(), nullable=False),
        sa.Column("contradictory_claim_ids", sa.JSON(), nullable=False),
        sa.Column("support_dimensions", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ("case_id", "direction", "status"):
        op.create_index(
            f"ix_identity_resolutions_{column}", "identity_resolutions", [column]
        )


def downgrade():
    op.drop_table("identity_resolutions")
    op.drop_table("evidence_relationships")
    op.drop_table("claim_contradictions")
    op.drop_table("case_aliases")
