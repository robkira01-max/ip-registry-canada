"""Fixtures partagées — Registre IP Canada."""
from __future__ import annotations
import os
import sys
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine as _real_ce
from sqlalchemy.orm import sessionmaker, Session
import sqlalchemy

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

# SQLite en mémoire pour les tests
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ.setdefault("JWT_PRIVATE_KEY_PATH", str(_backend.parent / "keys" / "private.pem"))
os.environ.setdefault("JWT_PUBLIC_KEY_PATH",  str(_backend.parent / "keys" / "public.pem"))
os.environ["DEBUG"] = "true"
os.environ["APP_ENV"] = "test"


def _sqlite_engine(url, **kwargs):
    kwargs.pop("pool_size", None)
    kwargs.pop("max_overflow", None)
    kwargs.pop("pool_pre_ping", None)
    return _real_ce(url, connect_args={"check_same_thread": False}, **kwargs)

sqlalchemy.create_engine = _sqlite_engine

from database import Base, get_db          # noqa: E402
from main import app                        # noqa: E402
from models.user import User, UserRole      # noqa: E402
from core.security import hash_password, create_access_token  # noqa: E402


@pytest.fixture(scope="session")
def engine():
    _engine = _sqlite_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=_engine)
    yield _engine
    _engine.dispose()


@pytest.fixture(scope="function")
def db(engine) -> Generator[Session, None, None]:
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    yield session
    session.close()
    try:
        transaction.rollback()
    except Exception:
        pass
    connection.close()


@pytest.fixture(scope="function")
def client(db: Session) -> TestClient:
    def _override():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = _override
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


def _make_user(db: Session, username: str, role: UserRole) -> User:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        user = User(
            username=username,
            email=f"{username}@test.local",
            hashed_password=hash_password("Test2026!"),
            role=role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@pytest.fixture
def admin_user(db: Session) -> User:
    return _make_user(db, "admin_test", UserRole.admin)


@pytest.fixture
def agent_user(db: Session) -> User:
    return _make_user(db, "agent_test", UserRole.agent)


@pytest.fixture
def readonly_user(db: Session) -> User:
    return _make_user(db, "readonly_test", UserRole.readonly)


@pytest.fixture
def admin_token(admin_user: User) -> str:
    return create_access_token(admin_user.username, admin_user.role.value)


@pytest.fixture
def agent_token(agent_user: User) -> str:
    return create_access_token(agent_user.username, agent_user.role.value)


@pytest.fixture
def auth_admin(admin_token: str) -> dict:
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def auth_agent(agent_token: str) -> dict:
    return {"Authorization": f"Bearer {agent_token}"}


@pytest.fixture
def readonly_token(readonly_user: User) -> str:
    return create_access_token(readonly_user.username, readonly_user.role.value)


@pytest.fixture
def auth_viewer(readonly_token: str) -> dict:
    return {"Authorization": f"Bearer {readonly_token}"}
