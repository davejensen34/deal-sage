"""add pilot users and audit attribution"""
from alembic import op
import sqlalchemy as sa

revision = "c92e6fc47d32"
down_revision = "b81d9ab36c21"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("users",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("provider",sa.String(50),nullable=False),sa.Column("subject",sa.String(255),nullable=False),sa.Column("email",sa.String(320)),sa.Column("display_name",sa.String(160),nullable=False),sa.Column("avatar_url",sa.String(500)),sa.Column("active",sa.Boolean(),nullable=False),sa.Column("last_login_at",sa.DateTime(timezone=True),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False),sa.UniqueConstraint("provider","subject",name="uq_users_provider_subject"))
    with op.batch_alter_table("audit_events") as batch:
        batch.add_column(sa.Column("user_id",sa.Integer(),nullable=True))
        batch.create_foreign_key("fk_audit_events_user_id","users",["user_id"],["id"])
        batch.create_index("ix_audit_events_user_id",["user_id"])


def downgrade():
    with op.batch_alter_table("audit_events") as batch:
        batch.drop_index("ix_audit_events_user_id")
        batch.drop_constraint("fk_audit_events_user_id",type_="foreignkey")
        batch.drop_column("user_id")
    op.drop_table("users")
