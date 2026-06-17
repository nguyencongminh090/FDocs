import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Cookie, Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.repositories.user_repository import UserRepository

bearer_scheme = HTTPBearer()

ALGORITHM = "HS256"


def create_access_token(user_id: uuid.UUID) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": str(user_id), "exp": expire}, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token() -> tuple[str, datetime]:
    import secrets
    token = secrets.token_urlsafe(64)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return token, expires_at


def decode_access_token(token: str) -> uuid.UUID:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return uuid.UUID(user_id_str)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> uuid.UUID:
    return decode_access_token(credentials.credentials)


def get_gemini_key(x_gemini_key: str | None = Header(None, alias="X-Gemini-Key")) -> str:
    if not x_gemini_key or not x_gemini_key.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="X-Gemini-Key header is required")
    return x_gemini_key


def get_response_language(x_response_language: str | None = Header(None, alias="X-Response-Language")) -> str | None:
    if x_response_language in ("vi", "en"):
        return x_response_language
    return None
