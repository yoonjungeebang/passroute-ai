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


app = FastAPI(
    title="PassRoute AI server",
    version="1.0.0",
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

app.include_router(evaluation_router)

app.include_router(stt.router)
app.include_router(voice_analysis.router)
app.include_router(face_analysis.router)

app.include_router(follow_up_router)

app.include_router(question_generate_router)

app.include_router(resume_router)
app.include_router(debate_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
