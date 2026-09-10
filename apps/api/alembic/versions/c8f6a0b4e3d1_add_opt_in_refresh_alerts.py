"""add opt-in in-app refresh alerts"""

from alembic import op
import sqlalchemy as sa

revision = "c8f6a0b4e3d1"
down_revision = "b7e5f9a3d2c0"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "alert_subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("owner_key", sa.String(320), nullable=False),
        sa.Column("source_key", sa.String(120), nullable=False),
        sa.Column("event_types", sa.JSON(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("owner_key", "source_key", name="uq_alert_subscription_owner_source"),
    )
    for column in ("user_id", "owner_key", "source_key", "active"):
        op.create_index(f"ix_alert_subscriptions_{column}", "alert_subscriptions", [column])
    op.create_table(
        "alert_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("subscription_id", sa.Integer(), sa.ForeignKey("alert_subscriptions.id"), nullable=False),
        sa.Column("source_refresh_id", sa.Integer(), sa.ForeignKey("source_refreshes.id"), nullable=False),
        sa.Column("event_type", sa.String(60), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("subscription_id", "source_refresh_id", "event_type", name="uq_alert_refresh_event"),
    )
    for column in ("subscription_id", "source_refresh_id", "event_type"):
        op.create_index(f"ix_alert_events_{column}", "alert_events", [column])


def downgrade():
    op.drop_table("alert_events")
    op.drop_table("alert_subscriptions")
