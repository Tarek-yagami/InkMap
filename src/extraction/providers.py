"""Provider presets for the OpenAI-compatible extractor.

Adding a new OpenAI-compatible provider (OpenRouter, Together, ...) means adding
one entry here; nothing in the extraction or pipeline layers changes.

Non-OpenAI providers get an explicit non-empty api_key fallback rather than
letting the client fall back to OPENAI_API_KEY: that fallback is meant for
OpenAI's own endpoint, and silently reusing it here would mean sending an
OpenAI credential to a third-party host.
"""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderConfig:
    base_url: str | None
    api_key: str | None
    models: list[str]


PROVIDERS: dict[str, ProviderConfig] = {
    "OpenAI": ProviderConfig(
        base_url=None,
        api_key=None,  # AsyncOpenAI reads OPENAI_API_KEY itself when api_key is None
        models=["gpt-4o-mini", "gpt-4o"],
    ),
    "Groq": ProviderConfig(
        base_url="https://api.groq.com/openai/v1",
        api_key=os.environ.get("GROQ_API_KEY") or "groq-api-key-not-set",
        models=["llama-3.3-70b-versatile", "llama-3.1-8b-instant"],
    ),
    "Ollama (local)": ProviderConfig(
        base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
        api_key="ollama",
        models=["llama3.1", "qwen2.5"],
    ),
}
