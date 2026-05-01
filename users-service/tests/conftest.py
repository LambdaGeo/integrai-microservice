import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import create_access_token, get_password_hash
from app.database import Base, get_db
from app.main import app
from app.models.usuario import AgenteProfile, Usuario


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


@pytest.fixture()
def client(db_session):
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
def active_user(db_session):
    user = Usuario(
        username="12345678901",
        email="agente@example.com",
        hashed_password=get_password_hash("senha12345"),
        is_active=True,
        is_staff=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def auth_headers(active_user):
    token = create_access_token({"sub": active_user.username})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def active_user_profile(db_session, active_user):
    profile = AgenteProfile(
        user_id=active_user.id,
        nome="Maria Agente",
        area="Area 1",
        ubs="UBS Centro",
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)
    return profile
