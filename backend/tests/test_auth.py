"""Tests authentification — Registre IP Canada."""
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from models.user import User, UserRole


class TestLogin:
    def test_login_success(self, client: TestClient, admin_user: User):
        r = client.post("/auth/login", data={
            "username": admin_user.username, "password": "Test2026!"
        })
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        assert data["role"] == "admin"

    def test_login_wrong_password(self, client: TestClient, admin_user: User):
        r = client.post("/auth/login", data={
            "username": admin_user.username, "password": "mauvais"
        })
        assert r.status_code == 401

    def test_login_unknown_user(self, client: TestClient):
        r = client.post("/auth/login", data={
            "username": "fantome", "password": "Test2026!"
        })
        assert r.status_code == 401

    def test_me_with_valid_token(self, client: TestClient, auth_admin: dict):
        r = client.get("/auth/me", headers=auth_admin)
        assert r.status_code == 200
        assert r.json()["role"] == "admin"

    def test_me_without_token(self, client: TestClient):
        r = client.get("/auth/me")
        assert r.status_code == 401


class TestUserManagement:
    def test_create_user_as_admin(self, client: TestClient, auth_admin: dict):
        r = client.post("/auth/users", json={
            "username": "nouveau_agent",
            "email": "agent@cipo.ca",
            "password": "Agent2026!",
            "role": "agent",
        }, headers=auth_admin)
        assert r.status_code == 201
        assert r.json()["role"] == "agent"

    def test_create_user_as_agent_forbidden(self, client: TestClient, auth_agent: dict):
        r = client.post("/auth/users", json={
            "username": "usurpateur",
            "email": "x@x.ca",
            "password": "Test2026!",
        }, headers=auth_agent)
        assert r.status_code == 403

    def test_list_users_as_admin(self, client: TestClient, auth_admin: dict, admin_user: User):
        r = client.get("/auth/users", headers=auth_admin)
        assert r.status_code == 200
        assert isinstance(r.json(), list)
