"""Builds a small made-up book PDF for tests and demos (no real textbook is included).

Layout: a cover, a table of contents that lists "Lesson N" lines, then three lessons.
Lesson 2 mentions "see Lesson 3" in the middle of a sentence, and there is a Lesson 10 heading,
so the tests can check that these do not confuse the splitter.
"""
import sys
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

LESSONS = {
    1: ("Basics of Networks", "A network connects computers so that they can share data. " * 12),
    2: ("Addresses", "Every device has an address. For routing rules, see Lesson 3 later in the book. " * 12),
    3: ("Routing", "A router forwards packets towards their destination. " * 12),
    10: ("Security Overview", "Security protects data from misuse. " * 12),
}


def build(path):
    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4

    def page(lines):
        y = height - 60
        for line in lines:
            c.drawString(50, y, line[:110]); y -= 16
        c.showPage()

    page(["SAMPLE BOOK", "A made-up book for tests"])
    page(["Contents"] + [f"Lesson {n}  {title} ........ {n + 2}" for n, (title, _) in LESSONS.items()])
    for n, (title, body) in LESSONS.items():
        words, lines, cur = body.split(), [], ""
        for w in words:
            if len(cur) + len(w) > 95:
                lines.append(cur); cur = w
            else:
                cur = f"{cur} {w}".strip()
        lines.append(cur)
        page([f"Lesson {n}: {title}"] + lines)
    c.save()


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "examples/sample_book.pdf")
