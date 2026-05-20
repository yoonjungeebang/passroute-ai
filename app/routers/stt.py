import logging
import time
from collections import deque

import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.stt_service import detect_voice, transcribe_audio, SAMPLE_RATE
from app.services.voice_analysis_service import count_filler_words
from app.core.redis_client import append_stt_transcript, set_voice_metric, incrby_voice_metric, get_voice_summary, get_full_transcript
from app.core.database import AsyncSessionLocal
from app.models.voice_analysis import VoiceAnalysis

logger = logging.getLogger(__name__)
router = APIRouter()

WPM_SLOW = 100
WPM_FAST = 180
WPM_WINDOW_SEC = 15
SILENCE_ALERT_SEC = 5.0
FEEDBACK_COOLDOWN_SEC = 5.0
CONSECUTIVE_FILLER_THRESHOLD = 3


@router.websocket("/ws/stt/{session_id}/{question_id}")
async def stt_websocket(websocket: WebSocket, session_id: str, question_id: str):
    await websocket.accept()
    audio_chunks = []

    speech_segments: deque = deque()
    consecutive_filler_segments = 0

    silence_start: float | None = None
    last_feedback: dict = {}

    def can_feedback(fb_type: str) -> bool:
        now = time.time()
        if now - last_feedback.get(fb_type, 0) >= FEEDBACK_COOLDOWN_SEC:
            last_feedback[fb_type] = now
            return True
        return False

    async def send_feedback(fb_type: str, message: str, **extra):
        if can_feedback(fb_type):
            await websocket.send_json({"status": "feedback", "type": fb_type, "message": message, **extra})

    try:
        while True:
            data = await websocket.receive_bytes()
            chunk = np.frombuffer(data, dtype=np.int16)
            now = time.time()

            if detect_voice(chunk):
                silence_start = None
                audio_chunks.append(chunk)
                await websocket.send_json({"status": "recording"})

            else:
                if silence_start is None:
                    silence_start = now

                silence_sec = round(now - silence_start, 2)
                await set_voice_metric(session_id, question_id, "silence_sec", silence_sec)

                if silence_sec > SILENCE_ALERT_SEC:
                    await send_feedback("silence", "답변 중 침묵이 길어지고 있습니다.")

                if audio_chunks:
                    try:
                        audio_buffer = np.concatenate(audio_chunks)
                        segment_sec = len(audio_buffer) / SAMPLE_RATE
                        text = await transcribe_audio(audio_buffer)

                        if text:
                            await append_stt_transcript(session_id, question_id, text)

                            # WPM 슬라이딩 윈도우
                            words = len([w for w in text.split() if w])
                            speech_segments.append((now, words, segment_sec))
                            cutoff = now - WPM_WINDOW_SEC
                            while speech_segments and speech_segments[0][0] < cutoff:
                                speech_segments.popleft()

                            total_words = sum(s[1] for s in speech_segments)
                            total_sec = sum(s[2] for s in speech_segments)
                            wpm = round(total_words / total_sec * 60, 1) if total_sec > 0 else 0.0
                            await set_voice_metric(session_id, question_id, "wpm", wpm)

                            # 필러워드 연속 카운트
                            filler_count = count_filler_words(text)
                            await incrby_voice_metric(session_id, question_id, "filler_count", filler_count)
                            if filler_count > 0:
                                consecutive_filler_segments += 1
                            else:
                                consecutive_filler_segments = 0

                            await websocket.send_json({
                                "status": "completed",
                                "text": text,
                                "session_id": session_id,
                                "question_id": question_id,
                                "wpm": wpm,
                                "filler_count": filler_count,
                            })

                            if 0 < wpm < WPM_SLOW:
                                await send_feedback("wpm_slow", "말이 느린 편입니다. 조금 더 빠른 속도로 답변해보세요.", wpm=wpm)
                            elif wpm > WPM_FAST:
                                await send_feedback("wpm_fast", "말이 빠릅니다. 조금만 천천히 말씀해 주세요.", wpm=wpm)

                            if consecutive_filler_segments >= CONSECUTIVE_FILLER_THRESHOLD:
                                await send_feedback("filler", "추임새가 많습니다. 의식적으로 줄여보세요.")

                    except Exception as e:
                        logger.error(f"STT 에러: {e}")
                        await websocket.send_json({"status": "error", "message": str(e)})
                    audio_chunks = []

                else:
                    await websocket.send_json({"status": "silence"})

    except WebSocketDisconnect:
        if audio_chunks:
            try:
                text = await transcribe_audio(np.concatenate(audio_chunks))
                if text:
                    await append_stt_transcript(session_id, question_id, text)
                    logger.info(f"[{session_id}:{question_id}] 최종 STT: {text}")
            except Exception as e:
                logger.error(f"최종 STT 에러: {e}")

        try:
            summary = await get_voice_summary(session_id, question_id)
            full_text = await get_full_transcript(session_id, question_id)
            async with AsyncSessionLocal() as db:
                db.add(VoiceAnalysis(
                    session_id=session_id,
                    question_id=question_id,
                    avg_wpm=summary["avg_wpm"],
                    silence_ratio=summary["silence_ratio"],
                    filler_count=summary["filler_count"],
                ))
                if full_text:
                    from sqlalchemy import text
                    await db.execute(
                        text("UPDATE interview_answers SET stt_text = :stt_text WHERE session_id = :session_id AND question_id = :question_id"),
                        {"stt_text": full_text, "session_id": session_id, "question_id": question_id},
                    )
                await db.commit()
            logger.info(f"[{session_id}:{question_id}] MySQL 저장 완료")
        except Exception as e:
            logger.error(f"MySQL 저장 에러: {e}")
