FILLER_WORDS = {"음", "어", "그", "저", "뭐", "아", "이", "그냥", "근데", "이제", "그러니까"}


def count_filler_words(text: str) -> int:
    tokens = [token.strip(".,!?~…。、·") for token in text.split()]
    return sum(1 for token in tokens if token in FILLER_WORDS)
