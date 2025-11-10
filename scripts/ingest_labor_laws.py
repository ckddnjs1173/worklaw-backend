# worklaw-backend/scripts/ingest_labor_laws.py
import os
import json
import time
import pathlib
import requests
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from database.connection import SessionLocal, Base, engine
from models.law import Law, LawArticle, LawArticleVersion

"""
환경변수:
  LAW_OC : 국가법령정보센터 Open API OC 값(이메일 ID)
예) setx LAW_OC yourid
"""

OPENAPI_BASE = "https://www.law.go.kr/DRF/lawService.do"

TARGET_LAWS = [
    "근로기준법",
    "최저임금법",
    "산업안전보건법",
    "남녀고용평등과 일·가정 양립 지원에 관한 법률",
    "근로자퇴직급여 보장법",
    "기간제 및 단시간근로자 보호 등에 관한 법률",
    "파견근로자보호 등에 관한 법률",
    "고용보험법",
    "임금채권보장법",
    "노동조합 및 노동관계조정법",
]

def fetch_law_json_by_name(oc: str, law_name: str) -> Dict[str, Any] | None:
    """
    현행법령(시행일) 본문 JSON 조회(target=eflaw, LM=법령명)
    문서: https://open.law.go.kr/LSO/openApi/guideResult.do?htmlName=lsEfYdInfoGuide
    """
    params = {
        "OC": oc,
        "target": "eflaw",
        "LM": law_name,
        "type": "JSON",
    }
    r = requests.get(OPENAPI_BASE, params=params, timeout=20)
    if r.status_code != 200:
        print(f"❌ HTTP {r.status_code} for {law_name}")
        return None
    try:
        return r.json()
    except Exception:
        # 일부 응답이 JSON string 형태일 수 있어 방어 처리
        try:
            return json.loads(r.text)
        except Exception as e:
            print(f"❌ JSON parse error for {law_name}: {e}")
            return None

def extract_articles_from_payload(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    응답 JSON 구조가 문서/버전에 따라 다소 차이날 수 있습니다.
    안전하게 '조문 목록'에 해당하는 배열을 탐색하고, 조문번호/표제/본문 텍스트를 생성합니다.
    원본 JSON은 LawArticle.current_json / LawArticleVersion.raw_json 에 저장합니다.
    """
    # 가능한 키 후보
    # 예시: payload["eflaw"]["조문"]["조문내용"] ... 구조가 다양할 수 있음.
    # 안전하게 문자열 결합을 위해 텍스트를 최대한 풀어 추출.
    articles: List[Dict[str, Any]] = []

    def flatten_text(node: Any) -> str:
        if node is None:
            return ""
        if isinstance(node, str):
            return node
        if isinstance(node, list):
            return "\n".join(flatten_text(x) for x in node)
        if isinstance(node, dict):
            parts = []
            for k, v in node.items():
                parts.append(flatten_text(v))
            return "\n".join(p for p in parts if p)
        return str(node)

    # 대략적인 구조 탐색
    root = payload.get("eflaw") or payload.get("law") or payload
    if not root:
        return articles

    # 조문 리스트 위치를 찾아봅니다.
    # 보편적으로 '조문' 배열 또는 '조문목록' 형태가 존재.
    candidates = []
    for key in ["조문", "조문목록", "장", "편", "항목"]:
        val = root.get(key)
        if val:
            candidates.append(val)

    # 후보들 중 리스트를 재귀적으로 순회하여 '조문' 성격의 dict들을 수집
    stack = candidates[:]
    while stack:
        cur = stack.pop(0)
        if isinstance(cur, list):
            for item in cur:
                stack.append(item)
        elif isinstance(cur, dict):
            # 조문 유력 키
            article_no = cur.get("조문번호") or cur.get("조") or cur.get("조문")
            content = cur.get("조문내용") or cur.get("내용") or cur.get("본문")
            title = cur.get("조문제목") or cur.get("제목")

            # 조문번호가 있으면 조문으로 간주
            if article_no:
                articles.append({
                    "article_no": str(article_no),
                    "title": str(title) if title else None,
                    "text": flatten_text(content),
                    "raw": cur,
                })
            else:
                # 하위 탐색
                for v in cur.values():
                    stack.append(v)

    # 중복/공백 제거
    uniq = {}
    for a in articles:
        key = a["article_no"]
        if key not in uniq:
            uniq[key] = a
    return list(uniq.values())

def upsert_law(db: Session, name: str, mst: str | None = None, law_id: str | None = None):
    row = db.query(Law).filter(Law.name == name).first()
    if not row:
        row = Law(name=name, mst=mst, law_id=law_id, status="ACTIVE")
        db.add(row)
        db.commit()
        db.refresh(row)
    return row

def upsert_articles(db: Session, law_row: Law, articles: List[Dict[str, Any]]):
    for a in articles:
        art = db.query(LawArticle).filter(
            LawArticle.law_id_fk == law_row.id,
            LawArticle.article_no == a["article_no"]
        ).first()
        if not art:
            art = LawArticle(
                law_id_fk=law_row.id,
                article_no=a["article_no"],
                title=a.get("title"),
                current_text=a.get("text"),
                current_json=a.get("raw"),
            )
            db.add(art)
            db.commit()
            db.refresh(art)
        else:
            # 변경 시 갱신
            art.title = a.get("title")
            art.current_text = a.get("text")
            art.current_json = a.get("raw")
            db.commit()

        # 버전 스냅샷(간단): 시행일 키를 찾으면 저장
        effective = None
        raw = a.get("raw") or {}
        for k in ["시행일자", "시행일", "effectiveDate"]:
            if isinstance(raw, dict) and raw.get(k):
                effective = str(raw.get(k))
                break

        ver = LawArticleVersion(
            article_id_fk=art.id,
            effective_date=effective,
            text=a.get("text"),
            raw_json=a.get("raw"),
        )
        db.add(ver)
        db.commit()

def ingest():
    oc = os.getenv("LAW_OC")
    if not oc:
        raise RuntimeError("환경변수 LAW_OC가 설정되어야 합니다. (예: setx LAW_OC yourid)")

    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        for name in TARGET_LAWS:
            print(f"▶ {name} 가져오는 중...")
            payload = fetch_law_json_by_name(oc, name)
            if not payload:
                print(f"⚠ {name} 응답 없음")
                continue
            articles = extract_articles_from_payload(payload)
            law_row = upsert_law(db, name)
            upsert_articles(db, law_row, articles)
            print(f"✅ {name}: {len(articles)}개 조문 저장")
            time.sleep(0.6)  # 매너 타임 & 과도 호출 방지
    finally:
        db.close()

if __name__ == "__main__":
    ingest()
+