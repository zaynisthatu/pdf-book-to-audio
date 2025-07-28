"""extract -> explain -> spoken script -> audio, one lesson at a time.

Output folders under --out:
  lessons/lec_NN.txt    the lesson text taken from the PDF
  explained/lec_NN.txt  step 1: simplified explanation
  scripts/lec_NN.txt    step 2: spoken script
  audio/lec_NN.wav|mp3  step 3: audio
Files that already exist are skipped, so an interrupted run can simply be started again.
"""
import logging
import time
import wave
from pathlib import Path

from . import chunking, extract
from .retry import with_retries

log = logging.getLogger("book_audio")
PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts"


def load_prompt(name: str) -> str:
    return (PROMPT_DIR / name).read_text(encoding="utf-8")


def write_audio(path: Path, chunks, ext: str, rate: int = 24000):
    tmp = path.with_suffix(path.suffix + ".tmp")
    if ext == "wav":
        with wave.open(str(tmp), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
            for c in chunks:
                w.writeframes(c)
    else:
        with open(tmp, "wb") as f:
            for c in chunks:
                f.write(c)
    tmp.replace(path)                                    # a half-written file never has the final name


def run(pdf_path, out_dir, text_backend, tts_backend, start=1, end=None, language="English",
        max_chars=4000, delay=0.0, extract_only=False, sleep=time.sleep):
    """Process lessons start..end. Returns {"done": [...], "skipped": [...], "missing": [...], "failed": {n: reason}}."""
    out = Path(out_dir)
    for sub in ("lessons", "explained", "scripts", "audio"):
        (out / sub).mkdir(parents=True, exist_ok=True)

    lessons = extract.extract_lessons(str(pdf_path))
    end = end if end is not None else (max(lessons) if lessons else 0)
    explain_prompt = load_prompt("explain.txt")
    script_prompt = load_prompt("script.txt")
    result = {"done": [], "skipped": [], "missing": [], "failed": {}}

    for n in range(start, end + 1):
        name = f"lec_{n:02d}"
        if n not in lessons:
            log.warning("lesson %d not found in the PDF", n)
            result["missing"].append(n)
            continue
        (out / "lessons" / f"{name}.txt").write_text(lessons[n], encoding="utf-8")
        if extract_only:
            result["done"].append(n)
            continue
        try:
            audio_path = out / "audio" / f"{name}.{tts_backend.ext}"
            if audio_path.exists():
                result["skipped"].append(n)
                continue

            explained_path = out / "explained" / f"{name}.txt"
            if not explained_path.exists():
                prompt = explain_prompt.format(lesson=n, language=language) + "\n\n" + lessons[n]
                explained_path.write_text(with_retries(lambda: text_backend.generate(prompt), sleep=sleep), encoding="utf-8")
            explained = explained_path.read_text(encoding="utf-8")

            script_path = out / "scripts" / f"{name}.txt"
            if not script_path.exists():
                prompt = script_prompt.format(lesson=n, language=language) + "\n\n" + explained
                script_path.write_text(with_retries(lambda: text_backend.generate(prompt), sleep=sleep), encoding="utf-8")
            script = script_path.read_text(encoding="utf-8")

            pieces = [with_retries(lambda c=c: tts_backend.synthesize(c), sleep=sleep)
                      for c in chunking.split_for_tts(script, max_chars)]
            write_audio(audio_path, pieces, tts_backend.ext, getattr(tts_backend, "rate", 24000))
            log.info("lesson %d done -> %s", n, audio_path.name)
            result["done"].append(n)
        except Exception as exc:                         # noqa: BLE001 - one bad lesson must not stop the book
            log.error("lesson %d failed: %s", n, exc)
            result["failed"][n] = str(exc)[:200]
        if delay:
            sleep(delay)
    return result
