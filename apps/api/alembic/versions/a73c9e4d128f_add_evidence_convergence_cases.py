"""add evidence convergence cases and claim lineage"""

from alembic import op
import sqlalchemy as sa


revision = "a73c9e4d128f"
down_revision = "f41a1b8c6d20"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "research_cases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("origin_strategy", sa.String(30), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("person_id", sa.Integer(), sa.ForeignKey("people.id")),
        sa.Column("business_id", sa.Integer(), sa.ForeignKey("businesses.id")),
        sa.Column(
            "transition_signal_id", sa.Integer(), sa.ForeignKey("transition_signals.id")
        ),
        sa.Column(
            "candidate_match_id", sa.Integer(), sa.ForeignKey("candidate_matches.id")
        ),
        sa.Column("research_budget", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.JSON(), nullable=False),
        sa.Column("stop_reason", sa.String(60)),
        sa.Column("stopped_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in (
        "origin_strategy",
        "status",
        "person_id",
        "business_id",
        "transition_signal_id",
        "candidate_match_id",
        "stop_reason",
    ):
        op.create_index(f"ix_research_cases_{column}", "research_cases", [column])

    op.create_table(
        "case_evidence",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_id", sa.Integer(), sa.ForeignKey("research_cases.id"), nullable=False),
        sa.Column("known_source_id", sa.Integer(), sa.ForeignKey("sources.id")),
        sa.Column("source_mode", sa.String(40), nullable=False),
        sa.Column("canonical_url", sa.String(1000), nullable=False),
        sa.Column("publisher", sa.String(200), nullable=False),
        sa.Column("source_type", sa.String(60), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("relevant_excerpt", sa.Text()),
        sa.Column("extracted_facts", sa.JSON(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("classification", sa.String(40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in (
        "case_id",
        "known_source_id",
        "source_mode",
        "source_type",
        "content_hash",
        "classification",
    ):
        op.create_index(f"ix_case_evidence_{column}", "case_evidence", [column])

    op.create_table(
        "evidence_claims",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_id", sa.Integer(), sa.ForeignKey("research_cases.id"), nullable=False),
        sa.Column("evidence_id", sa.Integer(), sa.ForeignKey("case_evidence.id"), nullable=False),
        sa.Column("subject_type", sa.String(50), nullable=False),
        sa.Column("predicate", sa.String(80), nullable=False),
        sa.Column("object_value", sa.JSON(), nullable=False),
        sa.Column("relationship_semantics", sa.String(60)),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("classification", sa.String(40), nullable=False),
        sa.Column("source_authority", sa.String(30), nullable=False),
        sa.Column("directness", sa.String(30), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in (
        "case_id",
        "evidence_id",
        "subject_type",
        "predicate",
        "relationship_semantics",
        "classification",
        "status",
    ):
        op.create_index(f"ix_evidence_claims_{column}", "evidence_claims", [column])

    op.create_table(
        "research_inferences",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_id", sa.Integer(), sa.ForeignKey("research_cases.id"), nullable=False),
        sa.Column("inference_type", sa.String(80), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("supporting_claim_ids", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("method", sa.String(30), nullable=False),
        sa.Column("provider", sa.String(60)),
        sa.Column("model", sa.String(120)),
        sa.Column("prompt_version", sa.String(80)),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ("case_id", "inference_type", "method", "status"):
        op.create_index(
            f"ix_research_inferences_{column}", "research_inferences", [column]
        )


def downgrade():
    op.drop_table("research_inferences")
    op.drop_table("evidence_claims")
    op.drop_table("case_evidence")
    op.drop_table("research_cases")
