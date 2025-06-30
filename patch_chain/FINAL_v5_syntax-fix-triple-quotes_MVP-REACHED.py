# SyntaxError: unterminated string literal -- long multiline Urdu/English text pasted
# directly into a single-double-quoted contents="..." argument
# FIX: use triple quotes for multiline content
response = client.models.generate_content(
    model="gemini-2.5-pro-preview-tts",
    contents="""Read aloud in a warm and friendly tone:
    [... long multi-paragraph lecture text ...]""",
)
# MVP REACHED -- basic single-call TTS generation confirmed working end-to-end.
