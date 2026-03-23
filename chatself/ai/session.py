"""
Interactive AI session — conversational reflection on your chat analysis.

Supports OpenAI (gpt-4o-mini default) and Anthropic (claude-haiku default).
Raw messages are NEVER sent. Only the pre-computed context is used.
"""

from __future__ import annotations

from typing import Generator

SUPPORTED_PROVIDERS = ("openai", "anthropic")


class AISession:
    """Wraps an LLM provider for interactive conversation."""

    def __init__(self, context: str, provider: str = "openai", model: str | None = None):
        if provider not in SUPPORTED_PROVIDERS:
            raise ValueError(f"Provider must be one of {SUPPORTED_PROVIDERS}")
        self.provider = provider
        self.context  = context
        self.model    = model or _default_model(provider)
        self.history: list[dict] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def ask(self, user_message: str) -> str:
        """Send a message, return the assistant reply as a string."""
        self.history.append({"role": "user", "content": user_message})
        reply = self._call()
        self.history.append({"role": "assistant", "content": reply})
        return reply

    def stream(self, user_message: str) -> Generator[str, None, None]:
        """Send a message, yield reply tokens as they arrive."""
        self.history.append({"role": "user", "content": user_message})
        chunks: list[str] = []
        for chunk in self._stream_call():
            chunks.append(chunk)
            yield chunk
        self.history.append({"role": "assistant", "content": "".join(chunks)})

    def reset(self):
        """Clear conversation history (context is kept)."""
        self.history.clear()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _call(self) -> str:
        if self.provider == "openai":
            return self._openai_call()
        return self._anthropic_call()

    def _stream_call(self) -> Generator[str, None, None]:
        if self.provider == "openai":
            yield from self._openai_stream()
        else:
            yield from self._anthropic_stream()

    # ---- OpenAI ----

    def _openai_call(self) -> str:
        from openai import OpenAI
        client = OpenAI()
        response = client.chat.completions.create(
            model=self.model,
            messages=self._openai_messages(),
        )
        return response.choices[0].message.content or ""

    def _openai_stream(self) -> Generator[str, None, None]:
        from openai import OpenAI
        client = OpenAI()
        stream = client.chat.completions.create(
            model=self.model,
            messages=self._openai_messages(),
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    def _openai_messages(self) -> list[dict]:
        return [
            {"role": "system", "content": self.context},
            *self.history,
        ]

    # ---- Anthropic ----

    def _anthropic_call(self) -> str:
        import anthropic
        client = anthropic.Anthropic()
        message = client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=self.context,
            messages=self.history,
        )
        return message.content[0].text

    def _anthropic_stream(self) -> Generator[str, None, None]:
        import anthropic
        client = anthropic.Anthropic()
        with client.messages.stream(
            model=self.model,
            max_tokens=1024,
            system=self.context,
            messages=self.history,
        ) as stream:
            for text in stream.text_stream:
                yield text


def _default_model(provider: str) -> str:
    return {
        "openai":    "gpt-4o-mini",
        "anthropic": "claude-haiku-4-5",
    }[provider]
