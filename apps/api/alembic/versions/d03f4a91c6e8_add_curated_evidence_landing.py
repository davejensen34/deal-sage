"""add curated evidence landing"""
from alembic import op
import sqlalchemy as sa

revision = "d03f4a91c6e8"
down_revision = "c92e6fc47d32"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("acquisition_runs",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("source_key",sa.String(120),nullable=False),sa.Column("jurisdiction",sa.String(80),nullable=False),sa.Column("discovery_strategy",sa.String(30),nullable=False),sa.Column("status",sa.String(30),nullable=False),sa.Column("contract_fingerprint",sa.String(64),nullable=False),sa.Column("started_at",sa.DateTime(timezone=True),nullable=False),sa.Column("finished_at",sa.DateTime(timezone=True)),sa.Column("metrics",sa.JSON(),nullable=False),sa.Column("error",sa.Text()),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False))
    op.create_index("ix_acquisition_runs_source_key","acquisition_runs",["source_key"])
    op.create_index("ix_acquisition_runs_jurisdiction","acquisition_runs",["jurisdiction"])
    op.create_index("ix_acquisition_runs_discovery_strategy","acquisition_runs",["discovery_strategy"])
    op.create_index("ix_acquisition_runs_status","acquisition_runs",["status"])
    op.create_table("raw_artifacts",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("content_hash",sa.String(64),nullable=False),sa.Column("source_key",sa.String(120),nullable=False),sa.Column("source_record_id",sa.String(200)),sa.Column("canonical_url",sa.String(1000),nullable=False),sa.Column("retrieved_at",sa.DateTime(timezone=True),nullable=False),sa.Column("media_type",sa.String(120),nullable=False),sa.Column("byte_size",sa.Integer(),nullable=False),sa.Column("storage_key",sa.String(500),nullable=False,unique=True),sa.Column("contract_fingerprint",sa.String(64),nullable=False),sa.Column("request_metadata",sa.JSON(),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False),sa.UniqueConstraint("source_key","content_hash",name="uq_raw_source_content"))
    op.create_index("ix_raw_artifacts_content_hash","raw_artifacts",["content_hash"])
    op.create_index("ix_raw_artifacts_source_key","raw_artifacts",["source_key"])
    op.create_index("ix_raw_artifacts_source_record_id","raw_artifacts",["source_record_id"])
    op.create_table("run_artifacts",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("run_id",sa.Integer(),sa.ForeignKey("acquisition_runs.id"),nullable=False),sa.Column("artifact_id",sa.Integer(),sa.ForeignKey("raw_artifacts.id"),nullable=False),sa.UniqueConstraint("run_id","artifact_id",name="uq_run_artifact"))
    op.create_index("ix_run_artifacts_run_id","run_artifacts",["run_id"])
    op.create_index("ix_run_artifacts_artifact_id","run_artifacts",["artifact_id"])
    op.create_table("curated_records",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("artifact_id",sa.Integer(),sa.ForeignKey("raw_artifacts.id"),nullable=False),sa.Column("subject_key",sa.String(240),nullable=False),sa.Column("subject_type",sa.String(40),nullable=False),sa.Column("parser_version",sa.String(80),nullable=False),sa.Column("schema_version",sa.String(80),nullable=False),sa.Column("status",sa.String(30),nullable=False),sa.Column("normalized_data",sa.JSON(),nullable=False),sa.Column("errors",sa.JSON(),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False),sa.UniqueConstraint("artifact_id","subject_key","parser_version",name="uq_curated_artifact_subject_parser"))
    op.create_index("ix_curated_records_artifact_id","curated_records",["artifact_id"])
    op.create_index("ix_curated_records_subject_type","curated_records",["subject_type"])
    op.create_index("ix_curated_records_status","curated_records",["status"])
    op.create_table("field_lineage",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("curated_record_id",sa.Integer(),sa.ForeignKey("curated_records.id"),nullable=False),sa.Column("field_name",sa.String(160),nullable=False),sa.Column("raw_path",sa.String(500),nullable=False),sa.Column("source_value_hash",sa.String(64),nullable=False),sa.UniqueConstraint("curated_record_id","field_name",name="uq_curated_field_lineage"))
    op.create_index("ix_field_lineage_curated_record_id","field_lineage",["curated_record_id"])


def downgrade():
    op.drop_table("field_lineage")
    op.drop_table("curated_records")
    op.drop_table("run_artifacts")
    op.drop_table("raw_artifacts")
    op.drop_table("acquisition_runs")
