"""Integration test cho /api/auth/* — qua ASGI, UserRepository thay bằng fake in-memory.

Verify: status code, response schema, cookie refresh_token, password hashing thật (bcrypt).
"""
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.routes.auth import COOKIE_NAME
from app.services import auth_service


class _User:
    def __init__(self, email, hashed_password):
        self.id = uuid.uuid4()
        self.email = email
        self.hashed_password = hashed_password
        self.created_at = datetime.now(timezone.utc)
        self.refresh_token = None
        self.refresh_token_expires_at = None


class _FakeUserRepo:
    store: list = []

    def __init__(self, db=None):
        pass

    async def get_by_email(self, email):
        return next((u for u in self.store if u.email == email), None)

    async def create(self, email, hashed_password):
        user = _User(email, hashed_password)
        self.store.append(user)
        return user

    async def set_refresh_token(self, user_id, token, expires_at):
        user = next((u for u in self.store if u.id == user_id), None)
        if user:
            user.refresh_token = token
            user.refresh_token_expires_at = expires_at

    async def get_by_refresh_token(self, token):
        return next((u for u in self.store if u.refresh_token == token), None)

    async def clear_refresh_token(self, user_id):
        user = next((u for u in self.store if u.id == user_id), None)
        if user:
            user.refresh_token = None


@pytest.fixture(autouse=True)
def fake_repo(monkeypatch):
    _FakeUserRepo.store = []
    monkeypatch.setattr(auth_service, "UserRepository", _FakeUserRepo)
    yield _FakeUserRepo


class TestRegister:
    async def test_register_success(self, client, db_override):
        resp = await client.post(
            "/api/auth/register", json={"email": "new@example.com", "password": "password123"}
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["access_token"]
        assert body["token_type"] == "bearer"
        assert body["user"]["email"] == "new@example.com"
        assert COOKIE_NAME in resp.cookies

    async def test_register_duplicate_email_409(self, client, db_override, fake_repo):
        fake_repo.store.append(_User("dup@example.com", "x"))
        resp = await client.post(
            "/api/auth/register", json={"email": "dup@example.com", "password": "password123"}
        )
        assert resp.status_code == 409

    async def test_register_short_password_422(self, client, db_override):
        resp = await client.post(
            "/api/auth/register", json={"email": "new@example.com", "password": "short"}
        )
        assert resp.status_code == 422

    async def test_register_invalid_email_422(self, client, db_override):
        resp = await client.post(
            "/api/auth/register", json={"email": "bad", "password": "password123"}
        )
        assert resp.status_code == 422


class TestLogin:
    async def test_login_success(self, client, db_override):
        await client.post(
            "/api/auth/register", json={"email": "u@example.com", "password": "password123"}
        )
        resp = await client.post(
            "/api/auth/login", json={"email": "u@example.com", "password": "password123"}
        )
        assert resp.status_code == 200
        assert resp.json()["access_token"]
        assert COOKIE_NAME in resp.cookies

    async def test_login_wrong_password_401(self, client, db_override):
        await client.post(
            "/api/auth/register", json={"email": "u@example.com", "password": "password123"}
        )
        resp = await client.post(
            "/api/auth/login", json={"email": "u@example.com", "password": "wrongpassword"}
        )
        assert resp.status_code == 401

    async def test_login_unknown_email_401(self, client, db_override):
        resp = await client.post(
            "/api/auth/login", json={"email": "ghost@example.com", "password": "password123"}
        )
        assert resp.status_code == 401


class TestRefresh:
    async def test_refresh_with_valid_cookie(self, client, db_override):
        reg = await client.post(
            "/api/auth/register", json={"email": "u@example.com", "password": "password123"}
        )
        cookie = reg.cookies[COOKIE_NAME]
        resp = await client.post("/api/auth/refresh", cookies={COOKIE_NAME: cookie})
        assert resp.status_code == 200
        assert resp.json()["access_token"]

    async def test_refresh_without_cookie_401(self, client, db_override):
        resp = await client.post("/api/auth/refresh")
        assert resp.status_code == 401

    async def test_refresh_expired_token_401(self, client, db_override, fake_repo):
        user = _User("u@example.com", "x")
        user.refresh_token = "expired-token"
        user.refresh_token_expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        fake_repo.store.append(user)
        resp = await client.post("/api/auth/refresh", cookies={COOKIE_NAME: "expired-token"})
        assert resp.status_code == 401
