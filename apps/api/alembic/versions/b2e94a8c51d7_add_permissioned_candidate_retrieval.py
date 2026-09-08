"""add permissioned source-candidate retrieval lineage"""

from alembic import op
import sqlalchemy as sa


revision = "b2e94a8c51d7"
down_revision = "a1c83d9f04b2"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("source_candidates") as batch_op:
        batch_op.add_column(
            sa.Column("access_decision", sa.String(30), nullable=False, server_default="pending")
        )
        batch_op.add_column(sa.Column("access_decision_reason", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("access_decided_by", sa.String(160), nullable=True))
        batch_op.add_column(sa.Column("access_decided_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.create_index("ix_source_candidates_access_decision", ["access_decision"])
    with op.batch_alter_table("case_evidence") as batch_op:
        batch_op.add_column(sa.Column("raw_artifact_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_case_evidence_raw_artifact_id_raw_artifacts",
            "raw_artifacts",
            ["raw_artifact_id"],
            ["id"],
        )
        batch_op.create_index("ix_case_evidence_raw_artifact_id", ["raw_artifact_id"])


def downgrade():
    with op.batch_alter_table("case_evidence") as batch_op:
        batch_op.drop_index("ix_case_evidence_raw_artifact_id")
        batch_op.drop_constraint(
            "fk_case_evidence_raw_artifact_id_raw_artifacts", type_="foreignkey"
        )
        batch_op.drop_column("raw_artifact_id")
    with op.batch_alter_table("source_candidates") as batch_op:
        batch_op.drop_index("ix_source_candidates_access_decision")
        batch_op.drop_column("access_decided_at")
        batch_op.drop_column("access_decided_by")
        batch_op.drop_column("access_decision_reason")
        batch_op.drop_column("access_decision")
