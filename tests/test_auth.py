import pytest
from httpx import AsyncClient, ASGITransport

@pytest.mark.asyncio
async def test_login_success(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/auth/login", json={"username": "admin", "password": "admin123!"})
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data and data["access_token"]
        assert data.get("token_type") == "bearer"

@pytest.mark.asyncio
async def test_login_fail(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/auth/login", json={"username": "admin", "password": "wrong"})
        assert res.status_code in (400, 401)
