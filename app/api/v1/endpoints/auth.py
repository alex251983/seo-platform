# app/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import UserCreate, UserResponse
from app.schemas.token import Token
from app.crud.user import create_user, authenticate_user
from app.core.security import create_access_token
from app.core.db import get_async_session

router = APIRouter()


# === Модели для запросов/ответов ===
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=64)


@router.post(
    "/register",
    response_model=UserResponse,
    dependencies=[Depends(RateLimiter(times=2, hours=1))]
)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_async_session)
):
    user = await create_user(db, user_in)
    return user


@router.post(
    "/login",
    response_model=Token,
    dependencies=[Depends(RateLimiter(times=5, minutes=1))]
)
async def login(
    credentials: LoginRequest,  # ← ← ← Pydantic-модель для JSON-тела
    db: AsyncSession = Depends(get_async_session)
):
    user = await authenticate_user(db, credentials.email, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        scopes=["user"]
    )
    return {"access_token": access_token, "token_type": "bearer"}
