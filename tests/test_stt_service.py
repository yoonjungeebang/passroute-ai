import struct
import wave

import numpy as np

from app.services.stt_service import SAMPLE_RATE, numpy_to_wav_bytes


class TestNumpyToWavBytes:
    def test_returns_valid_wav(self):
        audio = np.zeros(1600, dtype=np.int16)
        wav_bytes = numpy_to_wav_bytes(audio)
        assert wav_bytes[:4] == b"RIFF"

    def test_wav_params(self):
        audio = np.zeros(SAMPLE_RATE, dtype=np.int16)
        wav_bytes = numpy_to_wav_bytes(audio)
        import io
        with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
            assert wf.getnchannels() == 1
            assert wf.getsampwidth() == 2
            assert wf.getframerate() == SAMPLE_RATE
            assert wf.getnframes() == SAMPLE_RATE

    def test_preserves_audio_data(self):
        audio = np.array([100, -100, 32767, -32768], dtype=np.int16)
        wav_bytes = numpy_to_wav_bytes(audio)
        import io
        with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
            raw = wf.readframes(4)
        recovered = np.frombuffer(raw, dtype=np.int16)
        np.testing.assert_array_equal(audio, recovered)
