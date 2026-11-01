from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

from app.schemas.resume import DocumentStoreRequest
from app.services.resume_parser import parse_resume
from app.services.resume_vector_store import search_candidates, store_resume

router = APIRouter(prefix="/resume", tags=["resume"])


@router.post("/process")
async def process_resume(user_id: str, file: UploadFile = File(...)):
    """파일 업로드 → 텍스트 추출 → 임베딩 저장 (직접 파일 업로드 시 사용)."""
    try:
        file_bytes = await file.read()
        raw_text = await run_in_threadpool(parse_resume, file_bytes, file.filename)
        await store_resume(user_id, raw_text)

        return {"status": "success", "user_id": user_id}

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"처리 중 오류: {e!s}")


@router.post("/documents/store")
async def store_document(body: DocumentStoreRequest):
    """추출된 텍스트를 직접 받아 임베딩 저장 (백엔드에서 텍스트 추출 후 호출)."""
    try:
        await store_resume(body.user_id, body.text)
        return {"status": "success", "user_id": body.user_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"문서 저장 중 오류: {e!s}")


@router.get("/search")
async def search(query: str, top_k: int = 5):
    results = await search_candidates(query, top_k)
    return {"query": query, "results": results}