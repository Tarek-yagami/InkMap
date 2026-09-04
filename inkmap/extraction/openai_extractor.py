"""OpenAI structured-output implementation of the Extractor protocol."""

from openai import AsyncOpenAI

from inkmap.schema import KnowledgeGraph

_PROMPT = """Extract the key entities and relationships from the following excerpt of a research paper.
Identify technologies, methods, concepts, people, organizations, and datasets as nodes, and describe how they
relate to each other as edges. Only include entities that are explicitly discussed in this excerpt.

Excerpt:
{chunk}
"""


class OpenAIExtractor:
    def __init__(self, model: str = "gpt-4o-mini", client: AsyncOpenAI | None = None) -> None:
        self._model = model
        self._client = client or AsyncOpenAI()

    async def extract(self, chunk: str) -> KnowledgeGraph:
        response = await self._client.beta.chat.completions.parse(
            model=self._model,
            messages=[{"role": "user", "content": _PROMPT.format(chunk=chunk)}],
            response_format=KnowledgeGraph,
        )
        return response.choices[0].message.parsed
