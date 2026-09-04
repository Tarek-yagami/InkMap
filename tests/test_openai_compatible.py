from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError

from src.extraction.openai_compatible import OpenAICompatibleExtractor


def _mock_response(content: str) -> MagicMock:
    return MagicMock(choices=[MagicMock(message=MagicMock(content=content))])


async def test_extract_parses_a_valid_json_response():
    extractor = OpenAICompatibleExtractor(model="test-model", api_key="test-key")
    extractor._client.chat.completions.create = AsyncMock(
        return_value=_mock_response('{"nodes": [{"name": "Transformer", "type": "Technology"}], "edges": []}')
    )
    graph = await extractor.extract("some chunk")
    assert graph.nodes[0].name == "Transformer"


async def test_extract_raises_clearly_on_malformed_json():
    extractor = OpenAICompatibleExtractor(model="test-model", api_key="test-key")
    extractor._client.chat.completions.create = AsyncMock(return_value=_mock_response("not json"))
    with pytest.raises(ValidationError):
        await extractor.extract("some chunk")


def test_construction_never_eagerly_fails_for_a_custom_base_url():
    # Ollama-style config: no real API key needed, must not raise at
    # construction time regardless of what's in the environment.
    OpenAICompatibleExtractor(model="llama3.1", base_url="http://localhost:11434/v1", api_key="ollama")
