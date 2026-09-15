"""Immutable case brief snapshots."""
from alembic import op
import sqlalchemy as sa

revision = "f170a0b1d835"
down_revision = "e168a0b1d834"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("case_brief_versions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_id", sa.Integer(), sa.ForeignKey("research_cases.id"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("request_key", sa.String(36), nullable=False, unique=True),
        sa.Column("actor", sa.String(160), nullable=False),
        sa.Column("actor_key", sa.String(64), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("changes", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("case_id", "version", name="uq_case_brief_version"))
    op.create_index("ix_case_brief_versions_case_id", "case_brief_versions", ["case_id"])


def downgrade():
    if op.get_bind().execute(sa.text("SELECT COUNT(*) FROM case_brief_versions")).scalar():
        raise RuntimeError("Cannot discard retained case brief versions")
    op.drop_table("case_brief_versions")
