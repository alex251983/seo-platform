import asyncio
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.main import app
from app.core.db import get_async_session
from app.models.base import Base
from app.models.seo_data.service import SEODataService
from app.models.seo_data.providers.xmlriver_provider import XMLRiverProvider
from app.models.seo_data.router import get_seo_service
import os

TEST_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://seo:seopass@localhost:5432/seodb_test"
)

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        yield session


def get_test_seo_service():
    service = SEODataService()
    service._xmlriver_provider = XMLRiverProvider(user_id="test", api_key="test_key")
    return service


app.dependency_overrides[get_async_session] = override_get_db
app.dependency_overrides[get_seo_service] = get_test_seo_service


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


@pytest.fixture
async def registered_user(client: AsyncClient) -> dict:
    await client.post("/api/v1/auth/register", json={
        "email": "testuser@example.com",
        "password": "TestPassword123",
        "full_name": "Test User"
    })
    login = await client.post("/api/v1/auth/login", json={
        "email": "testuser@example.com",
        "password": "TestPassword123"
    })
    token = login.json()["access_token"]
    return {"token": token, "email": "testuser@example.com"}
