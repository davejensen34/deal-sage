"""Persist bounded system-selected extraction batches."""
from alembic import op
import sqlalchemy as sa

revision = 'd201a0b1d839'
down_revision = 'c178a0b1d838'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('extraction_batches',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('case_id', sa.Integer(), sa.ForeignKey('research_cases.id'), nullable=False),
        sa.Column('request_key', sa.String(36), unique=True, nullable=False),
        sa.Column('actor', sa.String(160), nullable=False),
        sa.Column('actor_key', sa.String(100), nullable=False),
        sa.Column('plan', sa.JSON(), nullable=False),
        sa.Column('plan_hash', sa.String(64), nullable=False),
        sa.Column('status', sa.String(30), nullable=False),
        sa.Column('next_index', sa.Integer(), nullable=False),
        sa.Column('lease_key', sa.String(36)),
        sa.Column('recovery_after', sa.DateTime(timezone=True)),
        sa.Column('deadline', sa.DateTime(timezone=True)),
        sa.Column('stop_reason', sa.String(60)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False))
    op.create_index('ix_extraction_batches_case_id', 'extraction_batches', ['case_id'])


def downgrade():
    if op.get_bind().execute(sa.text('SELECT COUNT(*) FROM extraction_batches')).scalar():
        raise RuntimeError('Cannot discard retained extraction batch history')
    op.drop_table('extraction_batches')
