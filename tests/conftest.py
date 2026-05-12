import asyncio
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.main import app
from app.core.db import Base, get_async_session
from app.config import settings
from app.modules.seo_data.service import SEODataService
from app.modules.seo_data.providers.xmlriver_provider import XMLRiverProvider
from fastapi import Depends

TEST_DATABASE_URL = settings.DATABASE_URL + "_test"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def override_get_db():
    async with TestSessionLocal() as session:
        yield session

app.dependency_overrides[get_async_session] = override_get_db

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

def get_test_seo_service():
    service = SEODataService()
    # Заменяем провайдера на тестовый с нереальными ключами
    service._xmlriver_provider = XMLRiverProvider(user_id=123, api_key="test_key")
    return service

app.dependency_overrides[get_seo_service] = get_test_seo_service