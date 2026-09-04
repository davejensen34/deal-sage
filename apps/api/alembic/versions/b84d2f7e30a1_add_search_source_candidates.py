"""add bounded search provenance and source candidates"""

from alembic import op
import sqlalchemy as sa


revision = "b84d2f7e30a1"
down_revision = "a73c9e4d128f"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "research_queries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_id", sa.Integer(), sa.ForeignKey("research_cases.id"), nullable=False),
        sa.Column("query_text", sa.Text(), nullable=False),
        sa.Column("provider", sa.String(80), nullable=False),
        sa.Column("max_results", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("latency_ms", sa.Integer()),
        sa.Column("result_count", sa.Integer(), nullable=False),
        sa.Column("error_class", sa.String(120)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ("case_id", "provider", "status"):
        op.create_index(f"ix_research_queries_{column}", "research_queries", [column])

    op.create_table(
        "source_candidates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_id", sa.Integer(), sa.ForeignKey("research_cases.id"), nullable=False),
        sa.Column("canonical_url", sa.String(1000), nullable=False),
        sa.Column("domain", sa.String(255), nullable=False),
        sa.Column("publisher", sa.String(200)),
        sa.Column("likely_source_type", sa.String(60), nullable=False),
        sa.Column("geography", sa.JSON(), nullable=False),
        sa.Column("relevance_reason", sa.Text(), nullable=False),
        sa.Column("proposed_use", sa.String(80), nullable=False),
        sa.Column("discovered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("search_provider", sa.String(80), nullable=False),
        sa.Column("access_observations", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("promoted_source_id", sa.Integer(), sa.ForeignKey("sources.id")),
        sa.Column("promotion_reason", sa.Text()),
        sa.Column("promoted_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("case_id", "canonical_url", name="uq_source_candidate_case_url"),
    )
    for column in (
        "case_id",
        "domain",
        "likely_source_type",
        "proposed_use",
        "search_provider",
        "status",
        "promoted_source_id",
    ):
        op.create_index(f"ix_source_candidates_{column}", "source_candidates", [column])

    op.create_table(
        "source_candidate_discoveries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "candidate_id", sa.Integer(), sa.ForeignKey("source_candidates.id"), nullable=False
        ),
        sa.Column("query_id", sa.Integer(), sa.ForeignKey("research_queries.id"), nullable=False),
        sa.Column("result_rank", sa.Integer(), nullable=False),
        sa.UniqueConstraint(
            "candidate_id", "query_id", name="uq_candidate_query_discovery"
        ),
    )
    op.create_index(
        "ix_source_candidate_discoveries_candidate_id",
        "source_candidate_discoveries",
        ["candidate_id"],
    )
    op.create_index(
        "ix_source_candidate_discoveries_query_id",
        "source_candidate_discoveries",
        ["query_id"],
    )


def downgrade():
    op.drop_table("source_candidate_discoveries")
    op.drop_table("source_candidates")
    op.drop_table("research_queries")
