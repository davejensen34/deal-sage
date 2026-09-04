"""add evidence-backed research trails"""
from alembic import op
import sqlalchemy as sa

revision = "b81d9ab36c21"
down_revision = "e5995a7a1b19"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("target_profiles",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("name",sa.String(160),nullable=False),sa.Column("criteria",sa.JSON(),nullable=False),sa.Column("provenance",sa.JSON(),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False))
    op.create_table("research_trails",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("business_id",sa.Integer(),sa.ForeignKey("businesses.id"),nullable=False,unique=True),sa.Column("target_profile_id",sa.Integer(),sa.ForeignKey("target_profiles.id")),sa.Column("owner_research_ready",sa.Boolean(),nullable=False),sa.Column("readiness_explanation",sa.Text(),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False))
    op.create_index("ix_research_trails_owner_research_ready","research_trails",["owner_research_ready"])
    op.create_table("research_stages",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("trail_id",sa.Integer(),sa.ForeignKey("research_trails.id"),nullable=False),sa.Column("stage_type",sa.String(50),nullable=False),sa.Column("sequence",sa.Integer(),nullable=False),sa.Column("status",sa.String(30),nullable=False),sa.Column("confidence",sa.Integer()),sa.Column("source_id",sa.Integer(),sa.ForeignKey("sources.id")),sa.Column("person_id",sa.Integer(),sa.ForeignKey("people.id")),sa.Column("relationship_id",sa.Integer(),sa.ForeignKey("business_relationships.id")),sa.Column("evidence_refs",sa.JSON(),nullable=False),sa.Column("supporting_evidence",sa.JSON(),nullable=False),sa.Column("contradictions",sa.JSON(),nullable=False),sa.Column("missing_evidence",sa.JSON(),nullable=False),sa.Column("detail",sa.Text(),nullable=False),sa.Column("occurred_at",sa.DateTime(timezone=True),nullable=False))
    op.create_index("ix_research_stages_trail_id","research_stages",["trail_id"])
    op.create_index("ix_research_stages_stage_type","research_stages",["stage_type"])
    op.create_index("ix_research_stages_status","research_stages",["status"])


def downgrade():
    op.drop_table("research_stages")
    op.drop_table("research_trails")
    op.drop_table("target_profiles")
