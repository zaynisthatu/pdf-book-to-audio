"""Split a book PDF into numbered lessons.

The heading must be a line of its own: "Lesson 5", "Lecture 5: Title", "LESSON 5 - Title".
A table of contents also contains such lines, but its entries are one line long, so for every
number the longest block wins.
"""
import re
from typing import Dict

import pdfplumber

# A heading is a whole line: "Lesson 5", "Lesson 5.", "Lecture 5: Title", "LESSON 5 - Title" or "Lesson 5 Title"
# (a title without punctuation must start with a capital letter or digit). This keeps a sentence that was
# wrapped so that a line starts with "Lesson 3 later in the book." from being taken as a heading.
HEADING = re.compile(
    r"^[ \t]*(?:lesson|lecture)\s+(\d+)\b"
    r"(?:[ \t]*[:.\-\u2013\u2014][ \t]*\S[^\n]{0,80}"
    r"|[ \t]+(?-i:[A-Z0-9])[^\n]{0,80}"
    r"|[ \t]*[:.]?[ \t]*)$",
    re.IGNORECASE | re.MULTILINE)


def read_pdf_text(path: str) -> str:
    """Text of the whole PDF, read once, pages joined with newlines."""
    parts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                parts.append(text)
    return "\n".join(parts)


def split_lessons(text: str) -> Dict[int, str]:
    """Return {lesson number: text from its heading up to the next heading of any number}."""
    marks = [(m.start(), int(m.group(1))) for m in HEADING.finditer(text)]
    best: Dict[int, str] = {}
    for i, (start, number) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        block = text[start:end].strip()
        if len(block) > len(best.get(number, "")):
            best[number] = block
    return dict(sorted(best.items()))


def extract_lessons(pdf_path: str) -> Dict[int, str]:
    return split_lessons(read_pdf_text(pdf_path))
