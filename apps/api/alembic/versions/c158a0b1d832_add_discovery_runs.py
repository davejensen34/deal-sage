"""Persist discovery defaults, frozen plans and pre-call reservations."""
from alembic import op
import sqlalchemy as sa

revision = "c158a0b1d832"
down_revision = "b144f0a9c721"
branch_labels = None
depends_on = None


def timestamps():
    return [sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False)]


def upgrade():
    op.create_table("discovery_profiles", sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("settings", sa.JSON(), nullable=False), sa.Column("actor", sa.String(160), nullable=False), *timestamps())
    op.create_table("discovery_runs", sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("request_key", sa.String(36), nullable=False, unique=True),
        sa.Column("case_id", sa.Integer(), sa.ForeignKey("research_cases.id"), nullable=False, unique=True),
        sa.Column("profile_id", sa.Integer(), sa.ForeignKey("discovery_profiles.id")),
        sa.Column("plan", sa.JSON(), nullable=False), sa.Column("plan_hash", sa.String(64), nullable=False),
        sa.Column("actor", sa.String(160), nullable=False), sa.Column("status", sa.String(30), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False), sa.Column("next_slot", sa.Integer(), nullable=False),
        sa.Column("reserved_cents", sa.Integer(), nullable=False), sa.Column("deadline_at", sa.DateTime(timezone=True)), *timestamps())
    op.create_table("discovery_attempts", sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("discovery_runs.id"), nullable=False),
        sa.Column("request_key", sa.String(36), nullable=False), sa.Column("slot", sa.Integer(), nullable=False),
        sa.Column("actor", sa.String(160), nullable=False), sa.Column("status", sa.String(30), nullable=False),
        sa.Column("reserved_cents", sa.Integer(), nullable=False), sa.Column("recovery_after", sa.DateTime(timezone=True), nullable=False),
        sa.Column("result_count", sa.Integer()), sa.Column("error_code", sa.String(60)), *timestamps(),
        sa.UniqueConstraint("run_id", "request_key"))
    op.create_index("ix_discovery_attempts_run_id", "discovery_attempts", ["run_id"])


def downgrade():
    for table in ["discovery_attempts", "discovery_runs", "discovery_profiles"]:
        if op.get_bind().execute(sa.text(f"SELECT COUNT(*) FROM {table}")).scalar():
            raise RuntimeError("Cannot discard retained discovery plans or reservations")
    for table in ["discovery_attempts", "discovery_runs", "discovery_profiles"]:
        op.drop_table(table)
