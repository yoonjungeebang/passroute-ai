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


async def incrbyfloat_voice_metric(session_id: str, question_id: str, metric: str, value: float) -> None:
    r = get_redis()
    key = f"voice:{session_id}:{question_id}:{metric}"
    await r.incrbyfloat(key, value)
    await r.expire(key, VOICE_ANALYSIS_TTL)


async def get_full_transcript(session_id: str, question_id: str) -> str:
    r = get_redis()
    segments = await r.lrange(f"stt:{session_id}:{question_id}", 0, -1)
    return " ".join(segments)


FACE_ANALYSIS_TTL = 3600  # 1시간


async def set_face_metric(session_id: str, question_id: str, metric: str, value) -> None:
    """실시간 피드백용 최신값 저장 (덮어쓰기)"""
    r = get_redis()
    key = f"face:{session_id}:{question_id}:{metric}"
    await r.set(key, value, ex=FACE_ANALYSIS_TTL)


async def rpush_face_metric(session_id: str, question_id: str, metric: str, value) -> None:
    """리포트용 누적 리스트 저장"""
    r = get_redis()
    key = f"face:{session_id}:{question_id}:{metric}"
    await r.rpush(key, value)
    await r.expire(key, FACE_ANALYSIS_TTL)


async def incrby_face_metric(session_id: str, question_id: str, metric: str, value: int) -> None:
    r = get_redis()
    key = f"face:{session_id}:{question_id}:{metric}"
    await r.incrby(key, value)
    await r.expire(key, FACE_ANALYSIS_TTL)


async def get_face_summary(session_id: str, question_id: str) -> dict:
    r = get_redis()
    prefix = f"face:{session_id}:{question_id}"

    gaze_off_count_raw = await r.get(f"{prefix}:gaze_off_count")
    gaze_ratio_values = [float(v) for v in await r.lrange(f"{prefix}:gaze_ratio_values", 0, -1)]
    total_blink_raw = await r.get(f"{prefix}:total_blink_count")
    total_dur_raw = await r.get(f"{prefix}:total_duration_sec")

    total_blink = int(total_blink_raw) if total_blink_raw else 0
    total_dur = float(total_dur_raw) if total_dur_raw else 0.0
    avg_blink_per_min = round(total_blink / (total_dur / 60), 2) if total_dur > 0 else 0.0
    avg_gaze_ratio = round(sum(gaze_ratio_values) / len(gaze_ratio_values), 2) if gaze_ratio_values else 0.0

    return {
        "gaze_off_count": int(gaze_off_count_raw) if gaze_off_count_raw else 0,
        "avg_gaze_ratio": avg_gaze_ratio,
        "avg_blink_per_min": avg_blink_per_min,
    }


async def get_voice_summary(session_id: str, question_id: str) -> dict:
    r = get_redis()
    prefix = f"voice:{session_id}:{question_id}"

    total_words_raw = await r.get(f"{prefix}:total_words")
    total_sec_raw = await r.get(f"{prefix}:total_speech_sec")
    silence_values = [float(v) for v in await r.lrange(f"{prefix}:silence_values", 0, -1)]
    filler_raw = await r.get(f"{prefix}:filler_count")

    total_words = int(total_words_raw) if total_words_raw else 0
    total_speech_sec = float(total_sec_raw) if total_sec_raw else 0.0
    avg_wpm = round(total_words / total_speech_sec * 60, 2) if total_speech_sec > 0 else 0.0
    avg_silence_duration = round(sum(silence_values) / len(silence_values), 2) if silence_values else 0.0
    filler_count = int(filler_raw) if filler_raw else 0

    return {
        "avg_wpm": avg_wpm,
        "avg_silence_duration": avg_silence_duration,
        "filler_count": filler_count,
    }
