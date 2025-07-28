"""Checks the call shape of the real backends with stand-in clients. No network, no API key.
This shows the code calls the SDK the way I intend; it does not show that the live services accept the calls."""
import os
import sys
import types

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from book_audio import text_backends, tts_backends   # noqa: E402


class FakeClient:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.calls = []
        outer = self

        class Models:
            def generate_content(self, **kw):
                outer.calls.append(kw)
                inline = types.SimpleNamespace(data=b"\x01\x02" * 100)
                part = types.SimpleNamespace(inline_data=inline)
                cand = types.SimpleNamespace(content=types.SimpleNamespace(parts=[part]))
                return types.SimpleNamespace(text="generated text", candidates=[cand])
        self.models = Models()


@pytest.fixture()
def fake_genai(monkeypatch):
    from google import genai
    holder = {}
    def factory(api_key=None):
        holder["client"] = FakeClient(api_key)
        return holder["client"]
    monkeypatch.setattr(genai, "Client", factory)
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    return holder


def test_gemini_backends_need_a_key_from_the_environment(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="GOOGLE_API_KEY"):
        text_backends.GeminiText()
    with pytest.raises(RuntimeError, match="GOOGLE_API_KEY"):
        tts_backends.GeminiTTS()


def test_gemini_text_call(fake_genai, monkeypatch):
    monkeypatch.setenv("GEMINI_TEXT_MODEL", "some-model")
    b = text_backends.GeminiText()
    assert b.generate("hello") == "generated text"
    call = fake_genai["client"].calls[0]
    assert call["model"] == "some-model" and call["contents"] == "hello"
    assert fake_genai["client"].api_key == "test-key"


def test_gemini_tts_call_asks_for_audio_and_returns_the_pcm_bytes(fake_genai):
    b = tts_backends.GeminiTTS()
    assert b.synthesize("say this") == b"\x01\x02" * 100
    call = fake_genai["client"].calls[0]
    assert call["model"] == "gemini-2.5-flash-preview-tts"
    cfg = call["config"]
    assert list(cfg.response_modalities) == ["AUDIO"]
    assert cfg.speech_config.voice_config.prebuilt_voice_config.voice_name == "Zephyr"


def test_gtts_backend(monkeypatch):
    import gtts
    seen = {}
    class FakeG:
        def __init__(self, text, lang):
            seen["text"], seen["lang"] = text, lang
        def write_to_fp(self, fp):
            fp.write(b"ID3fake-mp3")
    monkeypatch.setattr(gtts, "gTTS", FakeG)
    b = tts_backends.GTTS(lang="ur")
    assert b.synthesize("salaam") == b"ID3fake-mp3"
    assert seen == {"text": "salaam", "lang": "ur"} and b.ext == "mp3"


def test_unknown_backend_names_are_rejected():
    with pytest.raises(ValueError):
        text_backends.get_text_backend("nope")
    with pytest.raises(ValueError):
        tts_backends.get_tts_backend("nope")
