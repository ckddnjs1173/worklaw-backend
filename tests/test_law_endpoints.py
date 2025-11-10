import pytest
from httpx import AsyncClient, ASGITransport

@pytest.mark.asyncio
async def test_law_list_and_articles(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1) 법령 목록 조회 (데이터 없을 수도 있음)
        res_list = await ac.get("/law/list")
        assert res_list.status_code == 200
        laws = res_list.json()
        assert isinstance(laws, list)

        if not laws:
            # 데이터가 비어도 엔드포인트 동작 검증은 통과로 간주
            return

        # 2) 첫 번째 항목으로 조문 조회
        first = laws[0]
        # 백엔드가 반환하는 필드명이 law_name 또는 name일 수 있어 둘 다 시도
        law_name = first.get("law_name") or first.get("name")
        assert law_name, "법령 이름 필드(law_name/name)를 응답에서 찾을 수 없습니다."

        res_articles = await ac.get("/law/articles", params={"law_name": law_name})
        assert res_articles.status_code == 200
        arts = res_articles.json()
        assert isinstance(arts, list)
        # 데이터가 있으면 조문 형태 간단 검증
        if arts:
            a0 = arts[0]
            assert "article_no" in a0 and "content" in a0
