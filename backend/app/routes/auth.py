from fastapi import APIRouter, Cookie, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middlewares.auth import get_current_user_id
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["auth"])

COOKIE_NAME = "refresh_token"
COOKIE_OPTS = {"httponly": True, "secure": True, "samesite": "strict", "max_age": 60 * 60 * 24 * 30}


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, response: Response, db: AsyncSession = Depends(get_db)):
    result = await AuthService(db).register(body.email, body.password)
    response.set_cookie(COOKIE_NAME, result["refresh_token"], **COOKIE_OPTS)
    return {"access_token": result["access_token"], "token_type": "bearer", "user": UserResponse.model_validate(result["user"])}


@router.post("/login")
async def login(body: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    result = await AuthService(db).login(body.email, body.password)
    response.set_cookie(COOKIE_NAME, result["refresh_token"], **COOKIE_OPTS)
    return TokenResponse(access_token=result["access_token"])


@router.post("/refresh")
async def refresh(refresh_token: str = Cookie(None), db: AsyncSession = Depends(get_db)):
    if not refresh_token:
        from fastapi import HTTPException
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token")
    access_token = await AuthService(db).refresh(refresh_token)
    return TokenResponse(access_token=access_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response, user_id=Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    await AuthService(db).logout(user_id)
    response.delete_cookie(COOKIE_NAME)
