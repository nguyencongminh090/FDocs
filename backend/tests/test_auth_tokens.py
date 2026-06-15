"""Unit test cho JWT helper + gemini-key dependency trong middlewares/auth."""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from jose import jwt

from app.config import settings
from app.middlewares.auth import (
    ALGORITHM,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    get_gemini_key,
)


class TestAccessToken:
    def test_roundtrip_preserves_user_id(self):
        user_id = uuid.uuid4()
        token = create_access_token(user_id)
        assert decode_access_token(token) == user_id

    def test_token_carries_expiry(self):
        token = create_access_token(uuid.uuid4())
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        assert "exp" in payload

    def test_invalid_token_raises_401(self):
        with pytest.raises(HTTPException) as exc:
            decode_access_token("not-a-real-token")
        assert exc.value.status_code == 401

    def test_token_signed_with_wrong_secret_rejected(self):
        forged = jwt.encode(
            {"sub": str(uuid.uuid4()), "exp": datetime.now(timezone.utc) + timedelta(minutes=15)},
            "wrong-secret",
            algorithm=ALGORITHM,
        )
        with pytest.raises(HTTPException) as exc:
            decode_access_token(forged)
        assert exc.value.status_code == 401

    def test_expired_token_rejected(self):
        expired = jwt.encode(
            {"sub": str(uuid.uuid4()), "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
            settings.SECRET_KEY,
            algorithm=ALGORITHM,
        )
        with pytest.raises(HTTPException) as exc:
            decode_access_token(expired)
        assert exc.value.status_code == 401

    def test_token_missing_sub_rejected(self):
        no_sub = jwt.encode(
            {"exp": datetime.now(timezone.utc) + timedelta(minutes=15)},
            settings.SECRET_KEY,
            algorithm=ALGORITHM,
        )
        with pytest.raises(HTTPException) as exc:
            decode_access_token(no_sub)
        assert exc.value.status_code == 401


class TestRefreshToken:
    def test_returns_token_and_future_expiry(self):
        token, expires_at = create_refresh_token()
        assert isinstance(token, str) and len(token) > 0
        assert expires_at > datetime.now(timezone.utc)

    def test_tokens_are_unique(self):
        t1, _ = create_refresh_token()
        t2, _ = create_refresh_token()
        assert t1 != t2


class TestGeminiKeyDependency:
    def test_valid_key_passthrough(self):
        assert get_gemini_key("AIza-some-key") == "AIza-some-key"

    def test_whitespace_only_key_rejected(self):
        with pytest.raises(HTTPException) as exc:
            get_gemini_key("   ")
        assert exc.value.status_code == 400
