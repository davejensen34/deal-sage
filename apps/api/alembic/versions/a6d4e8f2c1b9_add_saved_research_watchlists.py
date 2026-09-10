"""add analyst-owned saved research and watchlists"""

from alembic import op
import sqlalchemy as sa

revision = "a6d4e8f2c1b9"
down_revision = "f5c1d2e3a4b5"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "saved_research",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("owner_key", sa.String(320), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("criteria", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_saved_research_user_id", "saved_research", ["user_id"])
    op.create_index("ix_saved_research_owner_key", "saved_research", ["owner_key"])
    op.create_table(
        "watchlists",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("owner_key", sa.String(320), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("owner_key", "name", name="uq_watchlists_owner_name"),
    )
    op.create_index("ix_watchlists_user_id", "watchlists", ["user_id"])
    op.create_index("ix_watchlists_owner_key", "watchlists", ["owner_key"])
    op.create_table(
        "watchlist_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("watchlist_id", sa.Integer(), sa.ForeignKey("watchlists.id"), nullable=False),
        sa.Column("candidate_id", sa.Integer(), sa.ForeignKey("candidate_matches.id"), nullable=False),
        sa.Column("added_by_user_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("rationale", sa.Text()),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("watchlist_id", "candidate_id", name="uq_watchlist_candidate"),
    )
    op.create_index("ix_watchlist_entries_watchlist_id", "watchlist_entries", ["watchlist_id"])
    op.create_index("ix_watchlist_entries_candidate_id", "watchlist_entries", ["candidate_id"])


def downgrade():
    op.drop_table("watchlist_entries")
    op.drop_table("watchlists")
    op.drop_table("saved_research")
