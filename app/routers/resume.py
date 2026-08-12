from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

from app.services.resume_parser import parse_resume
from app.services.resume_vector_store import store_resume, search_candidates

router = APIRouter(prefix="/resume", tags=["resume"])


@router.post("/process")
async def process_resume(user_id: str, file: UploadFile = File(...)):
    try:
        file_bytes = await file.read()
        raw_text = await run_in_threadpool(parse_resume, file_bytes, file.filename)
        await store_resume(user_id, raw_text)

        return {"status": "success", "user_id": user_id}

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"처리 중 오류: {str(e)}")


@router.get("/search")
async def search(query: str, top_k: int = 5):
    results = await search_candidates(query, top_k)
    return {"query": query, "results": results}