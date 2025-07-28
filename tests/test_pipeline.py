import os
import sys
import wave

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

from book_audio import chunking, pipeline                                  # noqa: E402
from book_audio.retry import with_retries, is_quota_error                  # noqa: E402
from book_audio.text_backends import FakeText                              # noqa: E402
from book_audio.tts_backends import FakeTTS                                # noqa: E402
import make_sample_pdf                                                      # noqa: E402


@pytest.fixture()
def pdf(tmp_path):
    p = tmp_path / "book.pdf"
    make_sample_pdf.build(str(p))
    return p


def test_full_run_with_fake_backends(pdf, tmp_path):
    out = tmp_path / "out"
    r = pipeline.run(pdf, out, FakeText(), FakeTTS(), start=1, end=3, sleep=lambda s: None)
    assert r["done"] == [1, 2, 3] and not r["failed"] and not r["missing"]
    for n in (1, 2, 3):
        for sub, ext in (("lessons", "txt"), ("explained", "txt"), ("scripts", "txt"), ("audio", "wav")):
            assert (out / sub / f"lec_{n:02d}.{ext}").exists(), (sub, n)
    with wave.open(str(out / "audio" / "lec_01.wav")) as w:
        assert w.getnchannels() == 1 and w.getsampwidth() == 2 and w.getframerate() == 24000
        assert w.getnframes() > 0


def test_second_run_skips_finished_lessons(pdf, tmp_path):
    out = tmp_path / "out"
    pipeline.run(pdf, out, FakeText(), FakeTTS(), start=1, end=2, sleep=lambda s: None)
    r = pipeline.run(pdf, out, FakeText(), FakeTTS(), start=1, end=2, sleep=lambda s: None)
    assert r["skipped"] == [1, 2] and r["done"] == []


def test_missing_lesson_is_reported_not_fatal(pdf, tmp_path):
    r = pipeline.run(pdf, tmp_path / "out", FakeText(), FakeTTS(), start=3, end=5, sleep=lambda s: None)
    assert r["done"] == [3] and r["missing"] == [4, 5]


def test_extract_only_makes_no_api_calls(pdf, tmp_path):
    class Boom:
        ext = "wav"
        def generate(self, p): raise AssertionError("called")
        def synthesize(self, t): raise AssertionError("called")
    r = pipeline.run(pdf, tmp_path / "out", Boom(), Boom(), start=1, end=2, extract_only=True)
    assert r["done"] == [1, 2]
    assert not list((tmp_path / "out" / "audio").iterdir())


def test_one_failing_lesson_does_not_stop_the_book(pdf, tmp_path):
    class FailsOnLesson2(FakeText):
        def generate(self, prompt):
            if "lesson 2" in prompt.split("\n")[0].lower():
                raise RuntimeError("model said no")
            return super().generate(prompt)
    r = pipeline.run(pdf, tmp_path / "out", FailsOnLesson2(), FakeTTS(), start=1, end=3, sleep=lambda s: None)
    assert r["done"] == [1, 3] and list(r["failed"]) == [2]


def test_quota_errors_are_retried_with_growing_waits():
    calls, waits = {"n": 0}, []
    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise RuntimeError("429 RESOURCE_EXHAUSTED. You exceeded your current quota")
        return "ok"
    assert with_retries(flaky, attempts=5, base_delay=2.0, sleep=waits.append) == "ok"
    assert waits == [2.0, 4.0]


def test_other_errors_are_not_retried():
    calls = {"n": 0}
    def broken():
        calls["n"] += 1
        raise ValueError("bad input")
    with pytest.raises(ValueError):
        with_retries(broken, sleep=lambda s: None)
    assert calls["n"] == 1
    assert is_quota_error(RuntimeError("429 Too Many Requests"))
    assert not is_quota_error(RuntimeError("file not found"))


def test_the_prompt_placeholders_are_filled(pdf, tmp_path):
    seen = []
    class Spy(FakeText):
        def generate(self, prompt):
            seen.append(prompt); return super().generate(prompt)
    pipeline.run(pdf, tmp_path / "out", Spy(), FakeTTS(), start=2, end=2, language="Roman Urdu", sleep=lambda s: None)
    assert "{" not in seen[0].split("\n\n")[0]            # no unfilled {lesson} / {language}
    assert "lesson 2" in seen[0] and "Roman Urdu" in seen[0]


def test_chunking_respects_the_limit_and_keeps_all_text():
    text = " ".join(f"Sentence number {i} is here." for i in range(300))
    chunks = chunking.split_for_tts(text, max_chars=500)
    assert all(len(c) <= 500 for c in chunks) and len(chunks) > 1
    assert " ".join(chunks).split() == text.split()
    assert chunking.split_for_tts("short text", 500) == ["short text"]
    assert chunking.split_for_tts("   ", 500) == []
    assert all(len(c) <= 100 for c in chunking.split_for_tts("x" * 450, 100))


def test_long_script_becomes_several_tts_calls(pdf, tmp_path):
    calls = []
    class CountingTTS(FakeTTS):
        def synthesize(self, text):
            calls.append(len(text)); return super().synthesize(text)
    class LongText(FakeText):
        def generate(self, prompt):
            return "This is a sentence. " * 100
    pipeline.run(pdf, tmp_path / "out", LongText(), CountingTTS(), start=1, end=1, max_chars=500, sleep=lambda s: None)
    assert len(calls) > 3 and max(calls) <= 500
