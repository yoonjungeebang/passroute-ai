import asyncio
import logging

import cv2
import mediapipe as mp
import numpy as np

logger = logging.getLogger(__name__)

mp_face_mesh = mp.solutions.face_mesh

# EAR landmarks: [outer, upper-outer, upper-inner, inner, lower-inner, lower-outer]
LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

# Iris center landmarks (requires refine_landmarks=True)
LEFT_IRIS_CENTER = 468
RIGHT_IRIS_CENTER = 473

# Eye corner landmarks for iris gaze ratio
LEFT_EYE_OUTER = 33
LEFT_EYE_INNER = 133
RIGHT_EYE_INNER = 263
RIGHT_EYE_OUTER = 362

EAR_THRESHOLD = 0.25
NOSE_TIP = 1  # nose tip landmark for head centering check

POSITIVE_EMOTIONS = {"happy"}
NEGATIVE_EMOTIONS = {"sad", "angry", "fear", "disgust"}


def _ear(landmarks, eye_indices, w: int, h: int) -> float:
    pts = [(landmarks[i].x * w, landmarks[i].y * h) for i in eye_indices]
    p1, p2, p3, p4, p5, p6 = pts
    vertical = np.linalg.norm(np.array(p2) - np.array(p6)) + np.linalg.norm(np.array(p3) - np.array(p5))
    horizontal = 2.0 * np.linalg.norm(np.array(p1) - np.array(p4))
    return vertical / horizontal if horizontal > 0 else 0.0


def _iris_centered(lm) -> bool:
    try:
        if len(lm) <= RIGHT_IRIS_CENTER:
            return True
        left_outer_x = lm[LEFT_EYE_OUTER].x
        left_inner_x = lm[LEFT_EYE_INNER].x
        iris_left_x = lm[LEFT_IRIS_CENTER].x
        eye_w_l = abs(left_outer_x - left_inner_x)
        if eye_w_l > 0.005:
            ratio_l = (iris_left_x - min(left_outer_x, left_inner_x)) / eye_w_l
            if not (0.2 < ratio_l < 0.8):
                return False

        right_outer_x = lm[RIGHT_EYE_OUTER].x
        right_inner_x = lm[RIGHT_EYE_INNER].x
        iris_right_x = lm[RIGHT_IRIS_CENTER].x
        eye_w_r = abs(right_outer_x - right_inner_x)
        if eye_w_r > 0.005:
            ratio_r = (iris_right_x - min(right_outer_x, right_inner_x)) / eye_w_r
            if not (0.2 < ratio_r < 0.8):
                return False
    except Exception:
        pass
    return True


def analyze_frame(face_mesh, frame_bgr: np.ndarray) -> dict:
    h, w = frame_bgr.shape[:2]
    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    result = face_mesh.process(rgb)

    if not result.multi_face_landmarks:
        return {"face_detected": False, "gaze_on": False, "blink": False, "ear": 0.0}

    lm = result.multi_face_landmarks[0].landmark

    left_ear = _ear(lm, LEFT_EYE, w, h)
    right_ear = _ear(lm, RIGHT_EYE, w, h)
    avg_ear = (left_ear + right_ear) / 2.0
    blink = avg_ear < EAR_THRESHOLD

    nose_x = lm[NOSE_TIP].x
    face_centered = 0.25 < nose_x < 0.75
    gaze_on = face_centered and _iris_centered(lm)

    return {
        "face_detected": True,
        "gaze_on": gaze_on,
        "blink": blink,
        "ear": round(avg_ear, 3),
    }


async def analyze_emotion_async(frame_bgr: np.ndarray) -> str:
    loop = asyncio.get_event_loop()

    def _run() -> str:
        try:
            from deepface import DeepFace
            result = DeepFace.analyze(
                frame_bgr,
                actions=["emotion"],
                enforce_detection=False,
                silent=True,
            )
            if isinstance(result, list):
                result = result[0]
            return result.get("dominant_emotion", "neutral")
        except Exception as e:
            logger.debug(f"DeepFace 분석 실패: {e}")
            return "neutral"

    return await loop.run_in_executor(None, _run)


def classify_emotion(emotion: str) -> str:
    if emotion in POSITIVE_EMOTIONS:
        return "positive"
    if emotion in NEGATIVE_EMOTIONS:
        return "negative"
    return "neutral"
