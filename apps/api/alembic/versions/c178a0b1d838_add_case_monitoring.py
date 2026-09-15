"""Retain personal case monitoring dates and update history."""
from alembic import op
import sqlalchemy as sa

revision = 'c178a0b1d838'
down_revision = 'b174a0b1d837'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('case_monitoring',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('case_id', sa.Integer(), sa.ForeignKey('research_cases.id'), nullable=False),
        sa.Column('owner_key', sa.String(64), nullable=False),
        sa.Column('actor', sa.String(160), nullable=False),
        sa.Column('prior_id', sa.Integer(), sa.ForeignKey('case_monitoring.id'), unique=True),
        sa.Column('request_key', sa.String(36), nullable=False, unique=True),
        sa.Column('due_on', sa.Date(), nullable=False),
        sa.Column('state', sa.String(20), nullable=False),
        sa.Column('content', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False))
    for column in ['case_id', 'owner_key', 'due_on']:
        op.create_index(f'ix_case_monitoring_{column}', 'case_monitoring', [column])


def downgrade():
    if op.get_bind().execute(sa.text('SELECT COUNT(*) FROM case_monitoring')).scalar():
        raise RuntimeError('Cannot discard retained case monitoring history')
    op.drop_table('case_monitoring')
