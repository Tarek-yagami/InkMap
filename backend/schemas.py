"""API-facing models, distinct from src/schema.py's domain model. The final
graph result is returned as src.schema.KnowledgeGraph directly - it's already
a clean Pydantic model, no need to duplicate it here."""

from pydantic import BaseModel


class ProviderSummary(BaseModel):
    name: str
    models: list[str]


class JobStatusResponse(BaseModel):
    id: str
    status: str  # "running" | "complete" | "error"
    done: int
    total: int
    result: dict | None = None
    error: str | None = None
