"""Extractor for any OpenAI-compatible chat completions API (OpenAI, Groq, Ollama, ...).

Uses plain JSON-object responses validated against the KnowledgeGraph schema
client-side, rather than OpenAI's `.parse()` structured-output helper, since
strict JSON-schema mode isn't reliably supported across every OpenAI-compatible
provider. One class covers all of them; adding a new provider is a config entry
in providers.py, not a new extractor class.

Concurrent chunk extraction easily exceeds a provider's tokens-per-minute cap
(e.g. Groq's free tier caps some models at 8000 TPM). aiolimiter paces requests
against that budget proactively; the SDK's own retry-with-backoff (max_retries)
stays as a second line of defense for whatever a rough token estimate misses.
"""

from aiolimiter import AsyncLimiter
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

# Rough estimate (~4 chars/token) plus a flat buffer covering the prompt
# template and expected completion size. Doesn't need to be exact, just close
# enough to pace requests under a provider's tokens-per-minute cap.
_CHARS_PER_TOKEN = 4
_TOKEN_ESTIMATE_BUFFER = 1500

# GPT-OSS models default to heavy hidden reasoning even for simple tasks: a
# one-word test request burned 89 reasoning tokens out of 107 completion
# tokens. reasoning_effort="low" cut that to 14 of 28 in the same test, an
# ~84% drop, with no loss in output quality for a plain extraction task.
# Other chat models don't recognize this parameter, so it's only sent when
# the model name says it's a GPT-OSS model.
_REASONING_MODEL_MARKER = "gpt-oss"


class OpenAICompatibleExtractor:
    def __init__(
        self,
        model: str,
        base_url: str | None = None,
        api_key: str | None = None,
        tokens_per_minute: int | None = None,
    ) -> None:
        self._model = model
        self._client = AsyncOpenAI(base_url=base_url, api_key=api_key, max_retries=5)
        self._limiter = AsyncLimiter(tokens_per_minute, 60) if tokens_per_minute else None

    async def extract(self, chunk: str) -> KnowledgeGraph:
        if self._limiter is not None:
            estimated_tokens = len(chunk) // _CHARS_PER_TOKEN + _TOKEN_ESTIMATE_BUFFER
            await self._limiter.acquire(estimated_tokens)

        extra_kwargs = {}
        if _REASONING_MODEL_MARKER in self._model:
            extra_kwargs["reasoning_effort"] = "low"

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": _PROMPT.format(chunk=chunk)}],
            response_format={"type": "json_object"},
            **extra_kwargs,
        )
        return KnowledgeGraph.model_validate_json(response.choices[0].message.content)
