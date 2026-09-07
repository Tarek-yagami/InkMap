"""Extractor for Anthropic's Claude models, via the Messages API.

Not OpenAI-compatible: a different request shape and a different structured-
output mechanism (forced tool use, rather than response_format={"type":
"json_object"}). Exists to prove the Extractor protocol is a real seam, not
just an OpenAI wrapper - pipeline.py and every caller work identically
regardless of which concrete extractor sits behind it.
"""

from anthropic import AsyncAnthropic

from src.extraction.prompt import EXTRACTION_TASK
from src.schema import KnowledgeGraph

_TOOL_NAME = "record_knowledge_graph"

_TOOL = {
    "name": _TOOL_NAME,
    "description": "Records the entities and relationships extracted from the excerpt.",
    "input_schema": KnowledgeGraph.model_json_schema(),
}


class AnthropicExtractor:
    def __init__(self, model: str, api_key: str | None = None) -> None:
        self._model = model
        self._client = AsyncAnthropic(api_key=api_key, max_retries=5)

    async def extract(self, chunk: str) -> KnowledgeGraph:
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=4096,
            tools=[_TOOL],
            tool_choice={"type": "tool", "name": _TOOL_NAME},
            messages=[{"role": "user", "content": f"{EXTRACTION_TASK}\n\nExcerpt:\n{chunk}"}],
        )
        tool_use = next(block for block in response.content if block.type == "tool_use")
        return KnowledgeGraph.model_validate(tool_use.input)
