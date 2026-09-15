"""Retain attributable case workflow decisions and correction history."""
from alembic import op
import sqlalchemy as sa
revision='b174a0b1d837'
down_revision='a172a0b1d836'
branch_labels=None
depends_on=None


def upgrade():
    op.create_table('case_decisions',sa.Column('id',sa.Integer(),primary_key=True),
        sa.Column('case_id',sa.Integer(),sa.ForeignKey('research_cases.id'),nullable=False),
        sa.Column('brief_id',sa.Integer(),sa.ForeignKey('case_brief_versions.id'),nullable=False),
        sa.Column('prior_id',sa.Integer(),sa.ForeignKey('case_decisions.id'),unique=True),
        sa.Column('request_key',sa.String(36),nullable=False,unique=True),
        sa.Column('actor',sa.String(160),nullable=False),sa.Column('actor_key',sa.String(64),nullable=False),
        sa.Column('content',sa.JSON(),nullable=False),
        sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),
        sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False))
    op.create_index('ix_case_decisions_case_id','case_decisions',['case_id'])


def downgrade():
    if op.get_bind().execute(sa.text('SELECT COUNT(*) FROM case_decisions')).scalar():
        raise RuntimeError('Cannot discard retained case decisions')
    op.drop_table('case_decisions')
