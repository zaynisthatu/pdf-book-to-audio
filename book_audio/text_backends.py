"""Backends for the two text steps (explain a lesson, then turn it into a spoken script)."""
import os


class FakeText:
    """For tests and dry runs: no network, deterministic output."""
    def generate(self, prompt: str) -> str:
        body = prompt.split("\n\n", 1)[-1]
        return "[generated] " + " ".join(body.split())[:400]


class GeminiText:
    """Gemini through the google-genai SDK. Needs GOOGLE_API_KEY.
    The default model is the one used in Jul 2025; set GEMINI_TEXT_MODEL if it has been renamed."""
    def __init__(self, model=None):
        from google import genai
        key = os.environ.get("GOOGLE_API_KEY")
        if not key:
            raise RuntimeError("Set GOOGLE_API_KEY in the environment (never put the key in code)")
        self.client = genai.Client(api_key=key)
        self.model = model or os.environ.get("GEMINI_TEXT_MODEL", "gemini-2.5-pro")

    def generate(self, prompt: str) -> str:
        response = self.client.models.generate_content(model=self.model, contents=prompt)
        return response.text


def get_text_backend(name: str):
    if name == "fake":
        return FakeText()
    if name == "gemini":
        return GeminiText()
    raise ValueError(f"unknown text backend: {name}")
