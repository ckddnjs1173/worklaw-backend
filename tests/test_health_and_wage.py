import pytest
from httpx import AsyncClient, ASGITransport

def _get_amount(body) -> int | None:
    """
    백엔드 응답 스키마 차이를 흡수:
    - { amount: 12345, year: 2030, ... }
    - { minimum_wage: 12345, year: 2030, ... }
    - { wage: 12345, year: 2030, ... }
    """
    for k in ("amount", "minimum_wage", "wage"):
        if k in body and body[k] is not None:
            try:
                return int(body[k])
            except Exception:
                pass
    return None

@pytest.mark.asyncio
async def test_health_ok(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/health")
        assert res.status_code == 200

@pytest.mark.asyncio
async def test_minimum_wage_crud_flow(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1) 로그인
        auth = await ac.post("/auth/login", json={"username": "admin", "password": "admin123!"})
        assert auth.status_code == 200
        token = auth.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2) 신규 연도 생성(예: 2030년 12,345원)
        create_res = await ac.post(
            "/admin/metadata/minimum-wage",
            headers=headers,
            json={"year": 2030, "amount": 12345}
        )
        assert create_res.status_code in (200, 201)

        # 3) 조회 (쿼리=2030)
        get_res = await ac.get("/metadata/minimum-wage", params={"year": 2030})
        assert get_res.status_code == 200
        body = get_res.json()
        assert str(body.get("year")) in ("2030", 2030)
        amt = _get_amount(body)
        assert amt == 12345, f"unexpected payload: {body}"

        # 4) 수정 (2030 → 13000)
        update_res = await ac.put(
            "/admin/metadata/minimum-wage/2030",
            headers=headers,
            json={"amount": 13000}
        )
        assert update_res.status_code in (200, 204)

        get_res2 = await ac.get("/metadata/minimum-wage", params={"year": 2030})
        assert get_res2.status_code == 200
        amt2 = _get_amount(get_res2.json())
        assert amt2 == 13000, f"unexpected payload after update: {get_res2.json()}"

        # 5) 이력 조회
        hist_res = await ac.get("/admin/metadata/minimum-wage/2030/history", headers=headers)
        assert hist_res.status_code == 200
        assert isinstance(hist_res.json(), list)

        # 6) 삭제
        del_res = await ac.delete("/admin/metadata/minimum-wage/2030", headers=headers)
        assert del_res.status_code in (200, 204)
