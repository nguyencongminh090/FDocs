"""Test fixtures dùng chung cho toàn bộ backend test suite.

Env vars phải được set TRƯỚC khi import bất kỳ module nào của app, vì
`app.config.Settings` và `app.database` đọc chúng ngay tại thời điểm import.
"""
import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/fdocs_test"
)
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:5173")

import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.database import get_db
from app.main import app
from app.middlewares.auth import get_current_user_id, get_gemini_key

TEST_USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
TEST_GEMINI_KEY = "test-gemini-key"


async def _fake_get_db():
    """get_db override — service layer được mock nên session không bao giờ được dùng thật."""
    yield None


@pytest_asyncio.fixture
async def client():
    """HTTP client gọi trực tiếp vào ASGI app, không cần mạng / không cần server thật."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_override():
    """Bật/tắt override cho auth + gemini-key dependency.

    Trả về callable: gọi authed() để giả lập user đã đăng nhập + có gemini key.
    """
    def authed(user_id=TEST_USER_ID, gemini_key=TEST_GEMINI_KEY):
        app.dependency_overrides[get_current_user_id] = lambda: user_id
        app.dependency_overrides[get_gemini_key] = lambda: gemini_key
        app.dependency_overrides[get_db] = _fake_get_db

    yield authed
    app.dependency_overrides.clear()


@pytest.fixture
def db_override():
    """Chỉ override get_db (cho route không cần auth dependency, ví dụ /auth/*)."""
    app.dependency_overrides[get_db] = _fake_get_db
    yield
    app.dependency_overrides.clear()
