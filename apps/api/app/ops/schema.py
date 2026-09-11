"""Upgrade DealSage schemas without silently accepting incomplete legacy databases."""

from __future__ import annotations

import argparse
from pathlib import Path

import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect

from app.core.database import Base
from app.domain import models  # noqa: F401


API_ROOT = Path(__file__).resolve().parents[2]


class LegacySchemaError(RuntimeError):
    """Raised when an unversioned schema is not a recognized DealSage shape."""


def alembic_config(database_url: str) -> Config:
    config = Config(str(API_ROOT / "alembic.ini"))
    config.attributes["database_url_explicit"] = True
    config.set_main_option("script_location", str(API_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    return config


def missing_model_columns(connection) -> set[tuple[str, str]]:
    database = inspect(connection)
    return {
        (table_name, column.name)
        for table_name, table in Base.metadata.tables.items()
        for column in table.columns
        if column.name not in {item["name"] for item in database.get_columns(table_name)}
    }


def _repair_recognized_legacy_columns(connection, missing: set[tuple[str, str]]) -> None:
    """Apply only the nullable/additive seams left by historical create_all startup."""
    operations = Operations(MigrationContext.configure(connection))
    if ("audit_events", "user_id") in missing:
        with operations.batch_alter_table("audit_events") as batch:
            batch.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
            batch.create_foreign_key("fk_audit_events_user_id", "users", ["user_id"], ["id"])
            batch.create_index("ix_audit_events_user_id", ["user_id"])
    if ("research_frontier_items", "proposal_id") in missing:
        with operations.batch_alter_table("research_frontier_items") as batch:
            batch.add_column(sa.Column("proposal_id", sa.Integer(), nullable=True))
            batch.create_foreign_key(
                "fk_research_frontier_items_proposal_id_model_proposals",
                "model_proposals", ["proposal_id"], ["id"],
            )
            batch.create_index("ix_research_frontier_items_proposal_id", ["proposal_id"])
    source_candidate_columns = {
        "access_decision": sa.Column(
            "access_decision", sa.String(30), nullable=False, server_default="pending"
        ),
        "access_decision_reason": sa.Column("access_decision_reason", sa.Text(), nullable=True),
        "access_decided_by": sa.Column("access_decided_by", sa.String(160), nullable=True),
        "access_decided_at": sa.Column("access_decided_at", sa.DateTime(timezone=True), nullable=True),
    }
    source_missing = [name for name in source_candidate_columns if ("source_candidates", name) in missing]
    if source_missing:
        with operations.batch_alter_table("source_candidates") as batch:
            for name in source_missing:
                batch.add_column(source_candidate_columns[name])
            if "access_decision" in source_missing:
                batch.create_index("ix_source_candidates_access_decision", ["access_decision"])
    if ("case_evidence", "raw_artifact_id") in missing:
        with operations.batch_alter_table("case_evidence") as batch:
            batch.add_column(sa.Column("raw_artifact_id", sa.Integer(), nullable=True))
            batch.create_foreign_key(
                "fk_case_evidence_raw_artifact_id_raw_artifacts",
                "raw_artifacts", ["raw_artifact_id"], ["id"],
            )
            batch.create_index("ix_case_evidence_raw_artifact_id", ["raw_artifact_id"])
    ai_execution_missing = [
        name for name in ("input_tokens", "output_tokens") if ("ai_executions", name) in missing
    ]
    if ai_execution_missing:
        with operations.batch_alter_table("ai_executions") as batch:
            for name in ai_execution_missing:
                batch.add_column(sa.Column(name, sa.Integer(), nullable=True))


RECOGNIZED_LEGACY_MISSING = {
    ("audit_events", "user_id"),
    ("research_frontier_items", "proposal_id"),
    ("source_candidates", "access_decision"),
    ("source_candidates", "access_decision_reason"),
    ("source_candidates", "access_decided_by"),
    ("source_candidates", "access_decided_at"),
    ("case_evidence", "raw_artifact_id"),
    ("ai_executions", "input_tokens"),
    ("ai_executions", "output_tokens"),
}


def upgrade_database(database_url: str) -> str:
    """Upgrade an empty/versioned database or adopt one exact legacy schema shape."""
    engine = create_engine(database_url)
    with engine.connect() as connection:
        tables = set(inspect(connection).get_table_names())
    domain_tables = set(Base.metadata.tables)
    if "alembic_version" in tables or not tables.intersection(domain_tables):
        command.upgrade(alembic_config(database_url), "head")
        return "upgraded"
    missing_tables = domain_tables - tables
    if missing_tables:
        raise LegacySchemaError(
            "Unversioned database is missing tables and cannot be adopted safely: "
            + ", ".join(sorted(missing_tables))
        )
    with engine.begin() as connection:
        missing = missing_model_columns(connection)
        unexpected = missing - RECOGNIZED_LEGACY_MISSING
        if unexpected:
            detail = ", ".join(f"{table}.{column}" for table, column in sorted(unexpected))
            raise LegacySchemaError(f"Unrecognized missing columns; refusing to stamp schema: {detail}")
        _repair_recognized_legacy_columns(connection, missing)
        # Legacy schemas also need the explicit unknown-activity state from M7.
        active = next(c for c in inspect(connection).get_columns("business_relationships") if c["name"] == "active")
        if not active["nullable"]:
            with Operations(MigrationContext.configure(connection)).batch_alter_table("business_relationships") as batch:
                batch.alter_column("active", existing_type=sa.Boolean(), nullable=True)
        remaining = missing_model_columns(connection)
        if remaining:
            detail = ", ".join(f"{table}.{column}" for table, column in sorted(remaining))
            raise LegacySchemaError(f"Legacy repair incomplete; refusing to stamp schema: {detail}")
    # Stamping occurs only after the current ORM shape has been verified. This
    # preserves Alembic as the authority for every subsequent upgrade.
    command.stamp(alembic_config(database_url), "head")
    return "adopted_legacy"


def main() -> None:
    parser = argparse.ArgumentParser(description="Upgrade the DealSage database schema")
    parser.add_argument("command", choices=["upgrade"])
    parser.add_argument("--database-url")
    args = parser.parse_args()
    if args.command == "upgrade":
        if args.database_url:
            database_url = args.database_url
        else:
            from app.core.config import get_settings
            database_url = get_settings().database_url
        print(upgrade_database(database_url))


if __name__ == "__main__":
    main()
