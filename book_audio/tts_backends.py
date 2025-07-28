"""Text-to-speech backends. Each one turns a short text into audio bytes.

  ext == "wav": backend returns raw PCM (16-bit, mono, `rate` Hz); the pipeline writes the WAV header.
  ext == "mp3": backend returns finished mp3 bytes; chunks are joined by simple concatenation.
"""
import io
import os


class FakeTTS:
    """Silence whose length follows the text length (10 ms per character). For tests."""
    ext = "wav"
    rate = 24000

    def synthesize(self, text: str) -> bytes:
        samples = int(self.rate * 0.01 * len(text))
        return b"\x00\x00" * samples


class GeminiTTS:
    """Gemini speech model through google-genai. Needs GOOGLE_API_KEY.
    Model and voice are the ones from the Jul 2025 scripts; override with GEMINI_TTS_MODEL / GEMINI_VOICE."""
    ext = "wav"
    rate = 24000

    def __init__(self, model=None, voice=None):
        from google import genai
        key = os.environ.get("GOOGLE_API_KEY")
        if not key:
            raise RuntimeError("Set GOOGLE_API_KEY in the environment (never put the key in code)")
        self.client = genai.Client(api_key=key)
        self.model = model or os.environ.get("GEMINI_TTS_MODEL", "gemini-2.5-flash-preview-tts")
        self.voice = voice or os.environ.get("GEMINI_VOICE", "Zephyr")

    def synthesize(self, text: str) -> bytes:
        from google.genai import types
        response = self.client.models.generate_content(
            model=self.model,
            contents=text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=self.voice)))))
        return response.candidates[0].content.parts[0].inline_data.data


class GTTS:
    """Free Google Translate voice through the gTTS package (needs internet, mp3 output)."""
    ext = "mp3"

    def __init__(self, lang=None):
        self.lang = lang or os.environ.get("GTTS_LANG", "en")

    def synthesize(self, text: str) -> bytes:
        from gtts import gTTS
        buf = io.BytesIO()
        gTTS(text=text, lang=self.lang).write_to_fp(buf)
        return buf.getvalue()


def get_tts_backend(name: str):
    if name == "fake":
        return FakeTTS()
    if name == "gemini":
        return GeminiTTS()
    if name == "gtts":
        return GTTS()
    raise ValueError(f"unknown tts backend: {name}")
