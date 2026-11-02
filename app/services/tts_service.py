import asyncio
import logging
import uuid

import boto3

from app.core.config import settings

logger = logging.getLogger(__name__)

_polly = boto3.client(
    "polly",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION,
)

_s3 = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION,
)


def _synthesize_and_upload_sync(text: str, s3_key: str) -> str:
    """Polly TTS 합성 + S3 업로드 (동기). asyncio.to_thread로 호출한다."""
    response = _polly.synthesize_speech(
        Text=text,
        OutputFormat="mp3",
        VoiceId=settings.TTS_VOICE,
        Engine="standard",
        LanguageCode="ko-KR",
    )
    audio_stream = response["AudioStream"].read()

    _s3.put_object(
        Bucket=settings.AWS_S3_BUCKET_NAME,
        Key=s3_key,
        Body=audio_stream,
        ContentType="audio/mpeg",
    )
    return f"https://{settings.AWS_S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"


async def synthesize_and_upload(text: str, prefix: str = "tts") -> str | None:
    """텍스트를 TTS로 변환하고 S3에 업로드하여 URL을 반환한다.

    TTS 비활성화 또는 실패 시 None을 반환하며, 예외를 전파하지 않는다.
    """
    if not settings.TTS_ENABLED or not text or not text.strip():
        return None
    try:
        s3_key = f"{prefix}/{uuid.uuid4()}.mp3"
        return await asyncio.to_thread(_synthesize_and_upload_sync, text, s3_key)
    except Exception:
        logger.exception("TTS 합성/업로드 실패: %.100s", text)
        return None


async def synthesize_batch(
    texts: list[str],
    prefix: str = "tts",
) -> list[str | None]:
    """여러 텍스트를 병렬로 TTS 변환한다."""
    return await asyncio.gather(
        *(synthesize_and_upload(t, prefix) for t in texts)
    )
