import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

from book_audio.extract import extract_lessons, split_lessons   # noqa: E402
import make_sample_pdf                                            # noqa: E402


def test_pdf_is_split_into_the_right_lessons(tmp_path):
    pdf = tmp_path / "book.pdf"
    make_sample_pdf.build(str(pdf))
    lessons = extract_lessons(str(pdf))
    assert sorted(lessons) == [1, 2, 3, 10]
    # the table of contents line must not win over the real lesson body
    assert "A network connects computers" in lessons[1]
    assert len(lessons[1]) > 200
    # an inline "see Lesson 3" must not start a new lesson, so lesson 2 keeps its full text
    assert " ".join(lessons[2].split()).count("Every device has an address") == 12   # lines wrap inside the PDF
    assert "A router forwards packets" not in lessons[2]
    # lesson 3 does not leak into lesson 10 and the other way round
    assert "Security protects data" not in lessons[3]
    assert "Security protects data" in lessons[10]


def test_lesson_1_does_not_match_lesson_10():
    text = "Lesson 1\nfirst body\nLesson 10\ntenth body\n"
    parts = split_lessons(text)
    assert parts[1] == "Lesson 1\nfirst body"
    assert parts[10] == "Lesson 10\ntenth body"


def test_headings_in_different_styles():
    text = "LECTURE 4: Title\nbody four\nlesson 5 - Other\nbody five"
    parts = split_lessons(text)
    assert list(parts) == [4, 5]
    assert parts[4].endswith("body four")


def test_text_without_headings_gives_nothing():
    assert split_lessons("just some text\nwithout headings") == {}


def test_a_wrapped_sentence_that_starts_with_lesson_n_is_not_a_heading():
    text = ("Lesson 2: Addresses\nEvery device has an address. For routing rules, see\n"
            "Lesson 3 later in the book. More text.\nLesson 3: Routing\nrouting body")
    parts = split_lessons(text)
    assert list(parts) == [2, 3]
    assert "More text." in parts[2]
    assert parts[3].endswith("routing body")
