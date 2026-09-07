"""Provider presets, each pointing create_extractor (factory.py) at the right
Extractor implementation for that provider's API shape.

Adding a new OpenAI-compatible provider (OpenRouter, Together, ...) means adding
one "openai_compatible" entry inside get_providers(); nothing in the extraction
or pipeline layers changes. A provider with a genuinely different API shape
(Claude's Messages API, Gemini, ...) needs its own Extractor class - see
anthropic_extractor.py for the one already added - but still slots in here as
just another entry, keyed by its own "kind".

Providers are built by a function, not a module-level dict, so environment
variables are read at call time rather than at import time. A module-level
dict would bake in whatever GROQ_API_KEY/OLLAMA_BASE_URL looked like at the
moment this module was first imported, which can be before .env has been
loaded depending on import order in the caller. Reading lazily makes this
correct regardless of that order.

Non-OpenAI providers get an explicit non-empty api_key fallback rather than
letting the client fall back to OPENAI_API_KEY: that fallback is meant for
OpenAI's own endpoint, and silently reusing it here would mean sending an
OpenAI credential to a third-party host.
"""

import os
from dataclasses import dataclass
from typing import Literal

ProviderKind = Literal["openai_compatible", "anthropic"]


@dataclass(frozen=True)
class ProviderConfig:
    kind: ProviderKind
    api_key: str | None
    models: list[str]
    base_url: str | None = None  # only meaningful for kind="openai_compatible"
    tokens_per_minute: int | None = None  # None means don't throttle client-side


def get_providers() -> dict[str, ProviderConfig]:
    return {
        "OpenAI": ProviderConfig(
            kind="openai_compatible",
            base_url=None,
            api_key=None,  # AsyncOpenAI reads OPENAI_API_KEY itself when api_key is None
            models=["gpt-4o-mini", "gpt-4o"],
        ),
        "Groq": ProviderConfig(
            kind="openai_compatible",
            base_url="https://api.groq.com/openai/v1",
            api_key=os.environ.get("GROQ_API_KEY") or "groq-api-key-not-set",
            models=["openai/gpt-oss-120b", "openai/gpt-oss-20b"],
            # Groq's free "on-demand" tier caps these models at 8000 TPM.
            # Conservative on purpose: better to pace slightly under the real
            # cap than to keep tripping it.
            tokens_per_minute=7000,
        ),
        "Ollama (local)": ProviderConfig(
            kind="openai_compatible",
            base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
            api_key="ollama",
            models=["llama3.1", "qwen2.5"],
        ),
        "Claude": ProviderConfig(
            kind="anthropic",
            api_key=os.environ.get("ANTHROPIC_API_KEY") or "anthropic-api-key-not-set",
            models=["claude-sonnet-5", "claude-haiku-4-5-20251001"],
        ),
    }
