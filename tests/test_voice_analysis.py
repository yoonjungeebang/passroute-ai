from app.services.voice_analysis_service import FILLER_WORDS, count_filler_words


class TestCountFillerWords:
    def test_no_filler(self):
        assert count_filler_words("오늘 면접 준비를 열심히 했습니다") == 0

    def test_single_filler(self):
        assert count_filler_words("음 잘 모르겠습니다") == 1

    def test_multiple_fillers(self):
        assert count_filler_words("음 어 그 저 뭐 그냥 했습니다") == 6

    def test_all_fillers(self):
        text = " ".join(FILLER_WORDS)
        assert count_filler_words(text) == len(FILLER_WORDS)

    def test_filler_with_punctuation(self):
        assert count_filler_words("음, 그러니까... 저는요") == 2

    def test_empty_string(self):
        assert count_filler_words("") == 0

    def test_filler_inside_word_not_counted(self):
        assert count_filler_words("그냥이라고 말하면 안돼요") == 0

    def test_repeated_fillers(self):
        assert count_filler_words("음 음 음 잘 모르겠어요") == 3
