import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.middlewares.auth import create_access_token, create_refresh_token
from app.repositories.user_repository import UserRepository

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, db: AsyncSession):
        self.repo = UserRepository(db)

    async def register(self, email: str, password: str) -> dict:
        if await self.repo.get_by_email(email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        hashed = pwd_context.hash(password)
        user = await self.repo.create(email=email, hashed_password=hashed)
        access_token = create_access_token(user.id)
        refresh_token, expires_at = create_refresh_token()
        await self.repo.set_refresh_token(user.id, refresh_token, expires_at)
        return {"user": user, "access_token": access_token, "refresh_token": refresh_token}

    async def login(self, email: str, password: str) -> dict:
        user = await self.repo.get_by_email(email)
        if not user or not pwd_context.verify(password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
        access_token = create_access_token(user.id)
        refresh_token, expires_at = create_refresh_token()
        await self.repo.set_refresh_token(user.id, refresh_token, expires_at)
        return {"access_token": access_token, "refresh_token": refresh_token}

    async def refresh(self, refresh_token: str) -> str:
        user = await self.repo.get_by_refresh_token(refresh_token)
        if not user or not user.refresh_token_expires_at:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
        if user.refresh_token_expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")
        return create_access_token(user.id)

    async def logout(self, user_id: uuid.UUID) -> None:
        await self.repo.clear_refresh_token(user_id)
