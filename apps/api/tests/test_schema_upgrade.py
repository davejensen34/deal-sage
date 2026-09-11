import sqlalchemy as sa
import pytest

from app.core.database import Base
from app.ops.schema import LegacySchemaError, upgrade_database
from app.ops.schema import alembic_config
from alembic import command
from app.services.seed import seed_database
from sqlalchemy.orm import Session


def sqlite_url(path) -> str:
    return f"sqlite:///{path}"


def test_upgrade_builds_empty_database_from_migrations(tmp_path):
    url = sqlite_url(tmp_path / "empty.db")
    assert upgrade_database(url) == "upgraded"
    with sa.create_engine(url).connect() as connection:
        tables = set(sa.inspect(connection).get_table_names())
        version = connection.execute(sa.text("SELECT version_num FROM alembic_version")).scalar_one()
    assert set(Base.metadata.tables).issubset(tables)
    assert version == "a729e10b3c42"


def test_upgrade_adopts_verified_unversioned_current_schema(tmp_path):
    url = sqlite_url(tmp_path / "legacy.db")
    engine = sa.create_engine(url)
    Base.metadata.create_all(engine)
    assert upgrade_database(url) == "adopted_legacy"
    with engine.connect() as connection:
        version = connection.execute(sa.text("SELECT version_num FROM alembic_version")).scalar_one()
    assert version == "a729e10b3c42"


def test_upgrade_refuses_partial_unversioned_database(tmp_path):
    url = sqlite_url(tmp_path / "partial.db")
    engine = sa.create_engine(url)
    Base.metadata.tables["businesses"].create(engine)
    with pytest.raises(LegacySchemaError, match="missing tables"):
        upgrade_database(url)


def test_activity_upgrade_preserves_history_and_allows_unknown(tmp_path):
    url = sqlite_url(tmp_path / "previous.db")
    command.upgrade(alembic_config(url), "d6f2a9c4e810")
    engine = sa.create_engine(url)
    with Session(engine) as db:
        seed_database(db)
    with engine.connect() as connection:
        before = connection.execute(sa.text("SELECT id, active FROM business_relationships ORDER BY id")).all()
    upgrade_database(url)
    with engine.begin() as connection:
        assert connection.execute(sa.text("SELECT id, active FROM business_relationships ORDER BY id")).all() == before
        connection.execute(sa.text("UPDATE business_relationships SET active = NULL WHERE id = :id"), {"id": before[0].id})
        assert connection.execute(sa.text("SELECT active FROM business_relationships WHERE id = :id"), {"id": before[0].id}).scalar_one() is None
    with pytest.raises(RuntimeError, match="activity is unknown"):
        command.downgrade(alembic_config(url), "d6f2a9c4e810")
