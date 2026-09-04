import os
os.environ["DATABASE_URL"]="sqlite:///:memory:"
os.environ["DEMO_MODE"]="false"
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.database import Base, get_db
from app.main import app
from app.services.seed import seed_database

engine=create_engine("sqlite://",connect_args={"check_same_thread":False},poolclass=StaticPool)
TestingSession=sessionmaker(bind=engine,expire_on_commit=False)
Base.metadata.create_all(engine)
with TestingSession() as db: seed_database(db)
def override_db():
    with TestingSession() as db: yield db
app.dependency_overrides[get_db]=override_db

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def override_db_session():
    with TestingSession() as db:
        yield db
