"""Persist linked follow-up plans and durable attempts."""
from alembic import op
import sqlalchemy as sa

revision = "a172a0b1d836"
down_revision = "f170a0b1d835"
branch_labels = None
depends_on = None


def timestamps():
    return [sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False)]


def upgrade():
    op.create_table("followup_runs", sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("request_key", sa.String(36), nullable=False, unique=True),
        sa.Column("case_id", sa.Integer(), sa.ForeignKey("research_cases.id"), nullable=False),
        sa.Column("frontier_id", sa.Integer(), sa.ForeignKey("research_frontier_items.id"), nullable=False, unique=True),
        sa.Column("actor_key", sa.String(64), nullable=False),
        sa.Column("plan", sa.JSON(), nullable=False), sa.Column("plan_hash", sa.String(64), nullable=False),
        sa.Column("actor", sa.String(160), nullable=False), sa.Column("status", sa.String(30), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False), sa.Column("next_slot", sa.Integer(), nullable=False),
        sa.Column("reserved_cents", sa.Integer(), nullable=False), sa.Column("deadline_at", sa.DateTime(timezone=True)), *timestamps())
    op.create_table("followup_attempts", sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("followup_runs.id"), nullable=False),
        sa.Column("request_key", sa.String(36), nullable=False), sa.Column("step_id", sa.Integer(), sa.ForeignKey("research_steps.id"), nullable=False, unique=True),
        sa.Column("slot", sa.Integer(), nullable=False),
        sa.Column("actor", sa.String(160), nullable=False), sa.Column("status", sa.String(30), nullable=False),
        sa.Column("reserved_cents", sa.Integer(), nullable=False), sa.Column("recovery_after", sa.DateTime(timezone=True), nullable=False),
        sa.Column("result_count", sa.Integer()), sa.Column("error_code", sa.String(60)), *timestamps(),
        sa.UniqueConstraint("run_id", "request_key"))
    op.create_index("ix_followup_attempts_run_id", "followup_attempts", ["run_id"])
    op.create_index("ix_followup_runs_case_id", "followup_runs", ["case_id"])

def downgrade():
    for table in ["followup_attempts", "followup_runs"]:
        if op.get_bind().execute(sa.text(f"SELECT COUNT(*) FROM {table}")).scalar():
            raise RuntimeError("Cannot discard retained follow-up history")
    op.drop_table("followup_attempts")
    op.drop_table("followup_runs")
