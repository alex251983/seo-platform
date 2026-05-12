from fastapi import APIRouter, Depends, HTTPException
from fastapi_limiter.depends import RateLimiter  # ← Добавлено
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import UserCreate, UserResponse
from app.schemas.token import Token
from app.crud.user import create_user, authenticate_user
from app.core.security import create_access_token
from app.core.db import get_async_session

router = APIRouter()

# 🔐 Регистрация: максимум 2 попытки в час (защита от спам-аккаунтов)
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

# 🔑 Вход: максимум 5 попыток в минуту (защита от подбора паролей)
@router.post(
    "/login",
    response_model=Token,
    dependencies=[Depends(RateLimiter(times=5, minutes=1))]
)
async def login(
    email: str,
    password: str,
    db: AsyncSession = Depends(get_async_session)
):
    user = await authenticate_user(db, email, password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}
