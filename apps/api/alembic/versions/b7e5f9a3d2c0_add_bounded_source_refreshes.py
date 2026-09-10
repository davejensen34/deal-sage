"""add durable bounded source refresh execution"""

from alembic import op
import sqlalchemy as sa

revision = "b7e5f9a3d2c0"
down_revision = "a6d4e8f2c1b9"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "source_refreshes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_key", sa.String(120), nullable=False),
        sa.Column("jurisdiction", sa.String(80), nullable=False),
        sa.Column("requested_by_user_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("requested_by_key", sa.String(320), nullable=False),
        sa.Column("requested_by_name", sa.String(160), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("record_limit", sa.Integer(), nullable=False),
        sa.Column("approved_cost_usd", sa.Float(), nullable=False),
        sa.Column("actual_cost_usd", sa.Float(), nullable=False),
        sa.Column("contract_fingerprint", sa.String(64), nullable=False),
        sa.Column("acquisition_run_id", sa.Integer(), sa.ForeignKey("acquisition_runs.id")),
        sa.Column("freshness_status", sa.String(60), nullable=False),
        sa.Column("freshness_reason", sa.Text()),
        sa.Column("result_summary", sa.JSON(), nullable=False),
        sa.Column("error_code", sa.String(120)),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ("source_key", "jurisdiction", "requested_by_user_id", "status", "acquisition_run_id"):
        op.create_index(f"ix_source_refreshes_{column}", "source_refreshes", [column])


def downgrade():
    op.drop_table("source_refreshes")
