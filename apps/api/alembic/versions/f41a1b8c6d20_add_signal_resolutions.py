"""add signal-first resolution outcomes"""

from alembic import op
import sqlalchemy as sa


revision = "f41a1b8c6d20"
down_revision = "d03f4a91c6e8"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "signal_resolutions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "starting_record_id",
            sa.Integer(),
            sa.ForeignKey("curated_records.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "business_record_id",
            sa.Integer(),
            sa.ForeignKey("curated_records.id"),
        ),
        sa.Column("outcome", sa.String(40), nullable=False),
        sa.Column("reason", sa.Text()),
        sa.Column("resolved_by", sa.String(160)),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_signal_resolutions_starting_record_id",
        "signal_resolutions",
        ["starting_record_id"],
    )
    op.create_index(
        "ix_signal_resolutions_business_record_id",
        "signal_resolutions",
        ["business_record_id"],
    )
    op.create_index(
        "ix_signal_resolutions_outcome", "signal_resolutions", ["outcome"]
    )


def downgrade():
    op.drop_table("signal_resolutions")
