"""Exposes provider/model choices to the frontend without ever leaking an
api_key, and with any deployment-hidden providers (e.g. Ollama on a public
Space, since a container has no route to a visitor's laptop) filtered out."""

from fastapi import APIRouter

from src.extraction.providers import get_providers

from backend.config import hidden_providers
from backend.schemas import ProviderSummary

router = APIRouter()


@router.get("/providers", response_model=list[ProviderSummary])
def list_providers() -> list[ProviderSummary]:
    hidden = hidden_providers()
    return [
        ProviderSummary(name=name, models=config.models)
        for name, config in get_providers().items()
        if name not in hidden
    ]
