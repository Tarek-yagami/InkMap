"""Extractor for any OpenAI-compatible chat completions API (OpenAI, Groq, Ollama, ...).

Uses plain JSON-object responses validated against the KnowledgeGraph schema
client-side, rather than OpenAI's `.parse()` structured-output helper, since
strict JSON-schema mode isn't reliably supported across every OpenAI-compatible
provider. One class covers all of them; adding a new provider is a config entry
in providers.py, not a new extractor class.
"""

from openai import AsyncOpenAI

from src.schema import KnowledgeGraph

_PROMPT = """Extract the key entities and relationships from the following excerpt of a research paper.
Identify technologies, methods, concepts, people, organizations, and datasets as nodes, and describe how they
relate to each other as edges. Only include entities that are explicitly discussed in this excerpt.

Respond with a single JSON object of exactly this shape, and nothing else:
{{"nodes": [{{"name": "...", "type": "Technology|Method|Concept|Person|Organization|Dataset"}}],
  "edges": [{{"source": "...", "target": "...", "relationship": "..."}}]}}

Excerpt:
{chunk}
"""


class OpenAICompatibleExtractor:
    def __init__(self, model: str, base_url: str | None = None, api_key: str | None = None) -> None:
        self._model = model
        self._client = AsyncOpenAI(base_url=base_url, api_key=api_key)

    async def extract(self, chunk: str) -> KnowledgeGraph:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": _PROMPT.format(chunk=chunk)}],
            response_format={"type": "json_object"},
        )
        return KnowledgeGraph.model_validate_json(response.choices[0].message.content)
