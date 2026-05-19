SAMPLE_RATE = 16000

FILLER_WORDS = {"음", "어", "그", "저", "뭐", "아", "이", "그냥", "근데", "이제", "그러니까"}


def calculate_wpm(text: str, speech_seconds: float) -> float:
    if speech_seconds <= 0:
        return 0.0
    words = [w for w in text.split() if w]
    if not words:
        return 0.0
    return round(len(words) / speech_seconds * 60, 2)


def count_filler_words(text: str) -> int:
    tokens = [token.strip(".,!?~…。、·") for token in text.split()]
    return sum(1 for token in tokens if token in FILLER_WORDS)
