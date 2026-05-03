from contextlib import asynccontextmanager
from fastapi import FastAPI
import chromadb
from app.core.config import settings
from app.services.embedder import OnnxEmbedder
from app.routers.evaluation import router as evaluation_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    app.state.chroma = chromadb.HttpClient(
        host=settings.CHROMADB_HOST,
        port=settings.CHROMADB_PORT,
    )
    app.state.embedder = OnnxEmbedder()
    yield
    # shutdown


app = FastAPI(
    title="PassRoute AI server",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(evaluation_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
