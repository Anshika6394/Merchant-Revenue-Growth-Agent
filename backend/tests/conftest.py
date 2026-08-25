import os
import tempfile
import pytest
from fastapi.testclient import TestClient

test_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
test_db.close()
os.environ["DATABASE_URL"] = f"sqlite:///{test_db.name}"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-with-at-least-32-bytes"

from app.db.session import Base, build_engine, get_db
from app.main import app

engine = build_engine(os.environ["DATABASE_URL"])

@pytest.fixture(autouse=True)
def database():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)

@pytest.fixture
def client():
    def override_db():
        from sqlalchemy.orm import Session
        with Session(engine) as session:
            yield session
    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def db():
    from sqlalchemy.orm import Session
    with Session(engine) as session:
        yield session
