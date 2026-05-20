import redis.asyncio as aioredis
from app.core.config import settings

_redis: aioredis.Redis | None = None

STT_TRANSCRIPT_TTL = 3600  # 1시간


async def init_redis():
    global _redis
    _redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)


async def close_redis():
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None


def get_redis() -> aioredis.Redis:
    if _redis is None:
        raise RuntimeError("Redis not initialized")
    return _redis


async def append_stt_transcript(session_id: str, question_id: str, text: str) -> None:
    r = get_redis()
    key = f"stt:{session_id}:{question_id}"
    await r.rpush(key, text)
    await r.expire(key, STT_TRANSCRIPT_TTL)


VOICE_ANALYSIS_TTL = 3600  # 1시간


async def set_voice_metric(session_id: str, question_id: str, metric: str, value: float) -> None:
    r = get_redis()
    key = f"voice:{session_id}:{question_id}:{metric}"
    await r.set(key, value, ex=VOICE_ANALYSIS_TTL)


async def incrby_voice_metric(session_id: str, question_id: str, metric: str, value: int) -> None:
    r = get_redis()
    key = f"voice:{session_id}:{question_id}:{metric}"
    await r.incrby(key, value)
    await r.expire(key, VOICE_ANALYSIS_TTL)


async def get_full_transcript(session_id: str, question_id: str) -> str:
    r = get_redis()
    segments = await r.lrange(f"stt:{session_id}:{question_id}", 0, -1)
    return " ".join(segments)


async def get_voice_summary(session_id: str, question_id: str) -> dict:
    r = get_redis()
    prefix = f"voice:{session_id}:{question_id}"

    wpm_raw = await r.get(f"{prefix}:wpm")
    silence_raw = await r.get(f"{prefix}:silence_sec")
    filler_raw = await r.get(f"{prefix}:filler_count")

    wpm = float(wpm_raw) if wpm_raw else 0.0
    silence_sec = float(silence_raw) if silence_raw else 0.0
    filler_count = int(filler_raw) if filler_raw else 0

    return {
        "avg_wpm": round(wpm, 2),
        "silence_ratio": silence_sec,
        "filler_count": filler_count,
    }
