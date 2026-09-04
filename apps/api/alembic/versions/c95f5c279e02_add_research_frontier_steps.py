"""add bounded research frontier and steps"""

from alembic import op
import sqlalchemy as sa


revision = "c95f5c279e02"
down_revision = "b84d2f7e30a1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "research_frontier_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_id", sa.Integer(), sa.ForeignKey("research_cases.id"), nullable=False),
        sa.Column("question_type", sa.String(80), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("supporting_claim_ids", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ("case_id", "question_type", "priority", "status"):
        op.create_index(
            f"ix_research_frontier_items_{column}", "research_frontier_items", [column]
        )

    op.create_table(
        "research_steps",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_id", sa.Integer(), sa.ForeignKey("research_cases.id"), nullable=False),
        sa.Column(
            "frontier_item_id",
            sa.Integer(),
            sa.ForeignKey("research_frontier_items.id"),
            nullable=False,
        ),
        sa.Column("step_number", sa.Integer(), nullable=False),
        sa.Column("action_type", sa.String(40), nullable=False),
        sa.Column("provider", sa.String(80)),
        sa.Column("model", sa.String(120)),
        sa.Column("prompt_version", sa.String(80)),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("latency_ms", sa.Integer()),
        sa.Column("cost_cents", sa.Integer(), nullable=False),
        sa.Column("result_summary", sa.JSON(), nullable=False),
        sa.Column("error_class", sa.String(120)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("case_id", "step_number", name="uq_research_step_case_number"),
    )
    for column in ("case_id", "frontier_item_id", "action_type", "status"):
        op.create_index(f"ix_research_steps_{column}", "research_steps", [column])


def downgrade():
    op.drop_table("research_steps")
    op.drop_table("research_frontier_items")
