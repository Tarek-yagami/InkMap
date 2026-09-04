"""Extraction interface: any LLM-backed entity/relationship extractor implements this.

The pipeline depends only on this Protocol, not on a concrete provider, so adding
support for a different model (Claude, a local model via Ollama, ...) means writing
a new class here, not touching pipeline.py.
"""

from typing import Protocol

from src.schema import KnowledgeGraph


class Extractor(Protocol):
    async def extract(self, chunk: str) -> KnowledgeGraph: ...
