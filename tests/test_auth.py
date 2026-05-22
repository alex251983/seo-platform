import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    response = await client.post("/api/v1/auth/register", json={
        "email": "user@example.com",
        "password": "Secret1234",
        "full_name": "Test User"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "user@example.com"
    assert "id" in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    payload = {"email": "dup@example.com", "password": "Secret1234"}
    await client.post("/api/v1/auth/register", json=payload)
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code in (400, 409, 422)


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "login@example.com",
        "password": "Secret1234"
    })
    response = await client.post("/api/v1/auth/login", json={
        "email": "login@example.com",
        "password": "Secret1234"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "wrong@example.com",
        "password": "Secret1234"
    })
    response = await client.post("/api/v1/auth/login", json={
        "email": "wrong@example.com",
        "password": "WrongPassword"
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_authenticated(client: AsyncClient, registered_user: dict):
    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {registered_user['token']}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == registered_user["email"]


@pytest.mark.asyncio
async def test_get_me_unauthenticated(client: AsyncClient):
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
