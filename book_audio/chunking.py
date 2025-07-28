import re


def split_for_tts(text: str, max_chars: int = 4000):
    """Split at sentence ends so that no chunk is longer than max_chars (a single longer sentence is cut)."""
    text = text.strip()
    if len(text) <= max_chars:
        return [text] if text else []
    sentences = re.split(r"(?<=[.!?\u0964\u06D4])\s+|\n{2,}", text)
    chunks, current = [], ""
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        while len(s) > max_chars:                       # one very long sentence
            if current:
                chunks.append(current); current = ""
            chunks.append(s[:max_chars]); s = s[max_chars:]
        if len(current) + len(s) + 1 > max_chars:
            chunks.append(current); current = s
        else:
            current = f"{current} {s}".strip()
    if current:
        chunks.append(current)
    return chunks
