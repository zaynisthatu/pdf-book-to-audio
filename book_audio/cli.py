import argparse
import logging
import sys

from . import pipeline
from .text_backends import get_text_backend
from .tts_backends import get_tts_backend


def main(argv=None):
    p = argparse.ArgumentParser(prog="book_audio", description="Turn the lessons of a book PDF into spoken audio.")
    p.add_argument("pdf")
    p.add_argument("--out", default="output")
    p.add_argument("--start", type=int, default=1)
    p.add_argument("--end", type=int, default=None, help="last lesson (default: the highest number found)")
    p.add_argument("--language", default="English", help='language of the explanation, for example "Roman Urdu"')
    p.add_argument("--text-backend", choices=["gemini", "fake"], default="gemini")
    p.add_argument("--tts-backend", choices=["gemini", "gtts", "fake"], default="gemini")
    p.add_argument("--max-chars", type=int, default=4000, help="longest text sent to the TTS in one call")
    p.add_argument("--delay", type=float, default=2.0, help="seconds to wait between lessons")
    p.add_argument("--extract-only", action="store_true", help="only split the PDF into lessons, no API calls")
    a = p.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    text = get_text_backend("fake") if a.extract_only else get_text_backend(a.text_backend)
    tts = get_tts_backend("fake") if a.extract_only else get_tts_backend(a.tts_backend)
    r = pipeline.run(a.pdf, a.out, text, tts, a.start, a.end, a.language, a.max_chars, a.delay, a.extract_only)
    print(f"done {len(r['done'])}  skipped {len(r['skipped'])}  missing {len(r['missing'])}  failed {len(r['failed'])}")
    for n, why in r["failed"].items():
        print(f"  lesson {n}: {why}")
    return 1 if r["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
