import pytest
from httpx import AsyncClient

@pytest.mark.anyio
async def test_register(client: AsyncClient):
    response = await client.post("/api/v1/auth/register", json={
        "email": "user@example.com",
        "password": "secret123",
        "full_name": "Test User"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "user@example.com"
    assert "id" in data

@pytest.mark.anyio
async def test_login(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "login@example.com",
        "password": "secret123"
    })
    response = await client.post("/api/v1/auth/login?email=login@example.com&password=secret123")
    assert response.status_code == 200
    assert "access_token" in response.json()