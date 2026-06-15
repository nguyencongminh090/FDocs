import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create(self, email: str, hashed_password: str) -> User:
        user = User(email=email, hashed_password=hashed_password)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def set_refresh_token(self, user_id: uuid.UUID, token: str, expires_at: datetime) -> None:
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(refresh_token=token, refresh_token_expires_at=expires_at)
        )
        await self.db.commit()

    async def get_by_refresh_token(self, token: str) -> User | None:
        result = await self.db.execute(select(User).where(User.refresh_token == token))
        return result.scalar_one_or_none()

    async def clear_refresh_token(self, user_id: uuid.UUID) -> None:
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(refresh_token=None, refresh_token_expires_at=None)
        )
        await self.db.commit()
