from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine
from app.routers import face_analysis, stt, voice_analysis
from app.routers.debate import router as debate_router
from app.routers.evaluation import router as evaluation_router
from app.routers.follow_up import router as follow_up_router
from app.routers.question_generate import router as question_generate_router
from app.routers.resume import router as resume_router
from app.services.embedder import get_embedder
from app.services.stt_service import close_http_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS resume_chunks (
                id          TEXT PRIMARY KEY,
                user_id     TEXT NOT NULL,
                content     TEXT NOT NULL,
                embedding   vector(768) NOT NULL
            )
        """))
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_resume_chunks_user
            ON resume_chunks (user_id)
        """))
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_resume_chunks_vec
            ON resume_chunks USING hnsw (embedding vector_cosine_ops)
        """))
        # job_descriptions 테이블은 크롤러가 생성·관리하므로 AI 서버에서 생성하지 않음
    app.state.embedder = get_embedder()
    yield
    await close_http_client()


tags_metadata = [
    {
        "name": "실시간 분석",
        "description": "프론트엔드에서 AI 서버로 **직접 연결**하는 WebSocket 엔드포인트. STT, 표정 분석 포함.",
    },
    {
        "name": "질문 생성",
        "description": "면접 질문 생성 및 꼬리질문 생성. 백엔드 서버 경유.",
    },
    {
        "name": "평가",
        "description": "답변 평가, 세션 요약, 음성/표정 분석 결과 조회. 백엔드 서버 경유.",
    },
    {
        "name": "리포트",
        "description": "면접 리포트 생성. 백엔드 서버 경유.",
    },
    {
        "name": "토론 면접",
        "description": "토론 면접 진행 관련 엔드포인트. 백엔드 서버 경유.",
    },
    {
        "name": "이력서",
        "description": "이력서 업로드, 임베딩 저장, 검색. 백엔드 서버 경유.",
    },
]

app = FastAPI(
    title="PassRoute AI server",
    version="1.0.0",
    openapi_tags=tags_metadata,
    lifespan=lifespan,
)

# CORS
origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()]
if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# 실시간 분석 (프론트엔드 직접 연결)
app.include_router(stt.router)
app.include_router(face_analysis.router)

# 질문 생성
app.include_router(question_generate_router)
app.include_router(follow_up_router)

# 평가 / 리포트
app.include_router(evaluation_router)
app.include_router(voice_analysis.router)

# 토론 면접
app.include_router(debate_router)

# 이력서
app.include_router(resume_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
