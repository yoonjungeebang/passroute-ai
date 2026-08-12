from langchain.text_splitter import RecursiveCharacterTextSplitter
from sqlalchemy import text

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.services.embedder import get_embedder


_embedder = None


def _get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = get_embedder()
    return _embedder


async def store_resume(user_id: str, raw_text: str) -> None:
    """이력서를 청킹 + 임베딩하여 PostgreSQL(pgvector)에 저장한다."""
    embedder = _get_embedder()

    # 기존 데이터 삭제
    async with AsyncSessionLocal() as session:
        await session.execute(
            text("DELETE FROM resume_chunks WHERE user_id = :uid"),
            {"uid": user_id},
        )

        # 텍스트 청킹
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = splitter.split_text(raw_text)

        # 임베딩 생성 및 삽입
        for i, chunk in enumerate(chunks):
            embedding = embedder.embed(chunk)
            await session.execute(
                text(
                    "INSERT INTO resume_chunks (id, user_id, content, embedding) "
                    "VALUES (:id, :uid, :content, :embedding)"
                ),
                {
                    "id": f"{user_id}_chunk_{i}",
                    "uid": user_id,
                    "content": chunk,
                    "embedding": str(embedding),
                },
            )

        await session.commit()


async def query_resume(user_id: str, search_query: str, n_results: int = 3) -> str:
    """PostgreSQL resumes 테이블에서 이력서 청크를 유사도 검색한다."""
    embedder = _get_embedder()
    query_embedding = embedder.embed(search_query)

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text(
                "SELECT content, 1 - (embedding <=> :embedding::vector) AS similarity "
                "FROM resume_chunks "
                "WHERE user_id = :uid "
                "ORDER BY embedding <=> :embedding::vector "
                "LIMIT :limit"
            ),
            {
                "embedding": str(query_embedding),
                "uid": user_id,
                "limit": n_results,
            },
        )
        rows = result.fetchall()

    if not rows:
        return ""

    return "\n".join(f"- {row.content[:300]}" for row in rows)


async def query_crawled_data(search_query: str, sources: list[str], n_results: int = 3) -> str:
    """PostgreSQL job_descriptions 테이블에서 크롤링 데이터를 유사도 검색한다."""
    if not search_query or not search_query.strip():
        return ""

    embedder = _get_embedder()
    query_embedding = embedder.embed(search_query)

    # source IN 절 동적 생성
    source_params = {f"s{i}": s for i, s in enumerate(sources)}
    source_placeholders = ", ".join(f":s{i}" for i in range(len(sources)))

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text(
                f"SELECT content, source, title "
                f"FROM job_descriptions "
                f"WHERE source IN ({source_placeholders}) "
                f"ORDER BY embedding <=> :embedding::vector "
                f"LIMIT :limit"
            ),
            {
                **source_params,
                "embedding": str(query_embedding),
                "limit": n_results,
            },
        )
        rows = result.fetchall()

    if not rows:
        return ""

    source_labels = {
        "tech_blog": "기술블로그",
        "jobkorea": "채용공고",
        "naver_news": "뉴스",
    }
    parts = []
    for row in rows:
        label = source_labels.get(row.source, row.source)
        title = row.title or ""
        parts.append(f"- [{label}] {title}: {row.content[:300]}")

    return "\n".join(parts)


async def search_candidates(query: str, top_k: int = 5) -> list[dict]:
    """PostgreSQL에서 이력서 유사도 검색으로 후보자를 찾는다."""
    embedder = _get_embedder()
    query_embedding = embedder.embed(query)

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text(
                "SELECT user_id, content, "
                "1 - (embedding <=> :embedding::vector) AS similarity "
                "FROM resume_chunks "
                "ORDER BY embedding <=> :embedding::vector "
                "LIMIT :limit"
            ),
            {
                "embedding": str(query_embedding),
                "limit": top_k * 3,  # 중복 user_id 제거를 위해 여유분 조회
            },
        )
        rows = result.fetchall()

    seen = set()
    candidates = []
    for row in rows:
        if row.user_id not in seen:
            seen.add(row.user_id)
            candidates.append({
                "user_id": row.user_id,
                "score": round(float(row.similarity), 4),
                "matched_text": row.content[:200],
            })
            if len(candidates) >= top_k:
                break

    return candidates
