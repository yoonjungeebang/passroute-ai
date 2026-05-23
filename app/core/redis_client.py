import redis.asyncio as aioredis
from app.core.config import settings

_redis: aioredis.Redis | None = None

STT_TRANSCRIPT_TTL = 3600  # 1시간
VOICE_ANALYSIS_TTL = 3600  # 1시간


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


async def set_voice_metric(session_id: str, question_id: str, metric: str, value: float) -> None:
    """실시간 피드백용 최신값 저장 (덮어쓰기)"""
    r = get_redis()
    key = f"voice:{session_id}:{question_id}:{metric}"
    await r.set(key, value, ex=VOICE_ANALYSIS_TTL)


async def rpush_voice_metric(session_id: str, question_id: str, metric: str, value: float) -> None:
    """리포트용 누적 리스트 저장"""
    r = get_redis()
    key = f"voice:{session_id}:{question_id}:{metric}"
    await r.rpush(key, value)
    await r.expire(key, VOICE_ANALYSIS_TTL)


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

    wpm_values = [float(v) for v in await r.lrange(f"{prefix}:wpm_values", 0, -1)]
    silence_values = [float(v) for v in await r.lrange(f"{prefix}:silence_values", 0, -1)]
    filler_raw = await r.get(f"{prefix}:filler_count")

    avg_wpm = round(sum(wpm_values) / len(wpm_values), 2) if wpm_values else 0.0
    avg_silence_duration = round(sum(silence_values) / len(silence_values), 2) if silence_values else 0.0
    filler_count = int(filler_raw) if filler_raw else 0

    return {
        "avg_wpm": avg_wpm,
        "silence_ratio": avg_silence_duration,
        "filler_count": filler_count,
    }
