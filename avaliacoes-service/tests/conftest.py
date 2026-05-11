import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import require_authenticated_user
from app.database import Base, get_db
from app.main import app


SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def disable_startup_db_creation():
    startup_handlers = list(app.router.on_startup)
    app.router.on_startup.clear()
    try:
        yield
    finally:
        app.router.on_startup[:] = startup_handlers


@pytest.fixture()
def auth_user():
    return {
        "id": 1,
        "username": "agente",
        "email": "agente@example.com",
        "is_active": True,
        "is_staff": True,
        "access_token": "test-token",
    }


@pytest.fixture()
def auth_overrides(monkeypatch, auth_user):
    async def override_current_user():
        return auth_user

    async def fake_authorized_gestante_ids(access_token, count=200):
        return [1, 2]

    async def fake_can_access_gestante(gestante_id, access_token):
        return int(gestante_id) in [1, 2]

    app.dependency_overrides[require_authenticated_user] = override_current_user

    for module_path in (
        "app.routers.avaliacoes",
        "app.routers.pilulas",
        "app.fhir.router",
    ):
        module = __import__(module_path, fromlist=[""])
        monkeypatch.setattr(module, "authorized_gestante_ids", fake_authorized_gestante_ids, raising=False)
        monkeypatch.setattr(module, "can_access_gestante", fake_can_access_gestante, raising=False)

    yield

    app.dependency_overrides.clear()


@pytest.fixture()
def client(db_session, auth_overrides):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def unauthenticated_client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
