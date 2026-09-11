import sqlalchemy as sa
import pytest

from app.core.database import Base
from app.ops.schema import LegacySchemaError, upgrade_database


def sqlite_url(path) -> str:
    return f"sqlite:///{path}"


def test_upgrade_builds_empty_database_from_migrations(tmp_path):
    url = sqlite_url(tmp_path / "empty.db")
    assert upgrade_database(url) == "upgraded"
    with sa.create_engine(url).connect() as connection:
        tables = set(sa.inspect(connection).get_table_names())
        version = connection.execute(sa.text("SELECT version_num FROM alembic_version")).scalar_one()
    assert set(Base.metadata.tables).issubset(tables)
    assert version == "d6f2a9c4e810"


def test_upgrade_adopts_verified_unversioned_current_schema(tmp_path):
    url = sqlite_url(tmp_path / "legacy.db")
    engine = sa.create_engine(url)
    Base.metadata.create_all(engine)
    assert upgrade_database(url) == "adopted_legacy"
    with engine.connect() as connection:
        version = connection.execute(sa.text("SELECT version_num FROM alembic_version")).scalar_one()
    assert version == "d6f2a9c4e810"


def test_upgrade_refuses_partial_unversioned_database(tmp_path):
    url = sqlite_url(tmp_path / "partial.db")
    engine = sa.create_engine(url)
    Base.metadata.tables["businesses"].create(engine)
    with pytest.raises(LegacySchemaError, match="missing tables"):
        upgrade_database(url)
