"""Deployment configuration, read lazily like src/extraction/providers.py:
env vars are resolved at call time, not import time, for the same reason
that module documents (correctness independent of import order)."""

import os


def hidden_providers() -> set[str]:
    """Provider names to exclude from GET /api/providers. Set via
    INKMAP_HIDDEN_PROVIDERS (comma-separated), e.g. "Ollama (local)" for
    any public deployment, since a container has no route to a visitor's
    laptop."""
    raw = os.environ.get("INKMAP_HIDDEN_PROVIDERS", "")
    return {name.strip() for name in raw.split(",") if name.strip()}


def dev_cors_origin() -> str | None:
    """Only set when running the Vite dev server without its proxy
    configured. Production is same-origin (frontend served by this same
    process) and needs no CORS at all."""
    return os.environ.get("INKMAP_DEV_CORS_ORIGIN")
