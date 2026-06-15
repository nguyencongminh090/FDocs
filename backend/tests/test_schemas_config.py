"""Unit test cho pydantic schema validation + config parsing."""
import pytest
from pydantic import ValidationError

from app.config import Settings
from app.schemas.auth import RegisterRequest


class TestRegisterRequest:
    def test_valid_request(self):
        req = RegisterRequest(email="user@example.com", password="longenough")
        assert req.email == "user@example.com"

    def test_password_too_short_rejected(self):
        with pytest.raises(ValidationError):
            RegisterRequest(email="user@example.com", password="short")

    def test_password_exactly_8_chars_accepted(self):
        req = RegisterRequest(email="user@example.com", password="12345678")
        assert req.password == "12345678"

    def test_invalid_email_rejected(self):
        with pytest.raises(ValidationError):
            RegisterRequest(email="not-an-email", password="longenough")


class TestSettings:
    def test_allowed_origins_single(self):
        s = Settings(
            DATABASE_URL="postgresql+asyncpg://x/y",
            SECRET_KEY="k",
            ALLOWED_ORIGINS="http://localhost:5173",
        )
        assert s.allowed_origins_list == ["http://localhost:5173"]

    def test_allowed_origins_multiple_trimmed(self):
        s = Settings(
            DATABASE_URL="postgresql+asyncpg://x/y",
            SECRET_KEY="k",
            ALLOWED_ORIGINS="http://a.com, http://b.com ,http://c.com",
        )
        assert s.allowed_origins_list == ["http://a.com", "http://b.com", "http://c.com"]

    def test_default_token_ttl(self):
        s = Settings(DATABASE_URL="postgresql+asyncpg://x/y", SECRET_KEY="k")
        assert s.ACCESS_TOKEN_EXPIRE_MINUTES == 15
        assert s.REFRESH_TOKEN_EXPIRE_DAYS == 30
