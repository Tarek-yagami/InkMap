from unittest.mock import AsyncMock, MagicMock

from src.extraction.anthropic_extractor import AnthropicExtractor


def _mock_response(tool_input: dict) -> MagicMock:
    tool_use_block = MagicMock(type="tool_use", input=tool_input)
    return MagicMock(content=[tool_use_block])


async def test_extract_parses_the_tool_call_input():
    extractor = AnthropicExtractor(model="test-model", api_key="test-key")
    extractor._client.messages.create = AsyncMock(
        return_value=_mock_response({"nodes": [{"name": "Transformer", "type": "Technology"}], "edges": []})
    )
    graph = await extractor.extract("some chunk")
    assert graph.nodes[0].name == "Transformer"


async def test_extract_forces_the_tool_call_and_names_it():
    extractor = AnthropicExtractor(model="test-model", api_key="test-key")
    mock_create = AsyncMock(return_value=_mock_response({"nodes": [], "edges": []}))
    extractor._client.messages.create = mock_create

    await extractor.extract("some chunk")

    _, kwargs = mock_create.call_args
    assert kwargs["tool_choice"] == {"type": "tool", "name": "record_knowledge_graph"}
    assert kwargs["tools"][0]["name"] == "record_knowledge_graph"


async def test_extract_picks_the_tool_use_block_even_if_not_first():
    # Claude can prepend a plain-text block (e.g. brief reasoning) before the
    # forced tool call; the extractor must not assume content[0] is the tool use.
    extractor = AnthropicExtractor(model="test-model", api_key="test-key")
    text_block = MagicMock(type="text", text="Sure, here you go.")
    tool_use_block = MagicMock(type="tool_use", input={"nodes": [], "edges": []})
    extractor._client.messages.create = AsyncMock(return_value=MagicMock(content=[text_block, tool_use_block]))

    graph = await extractor.extract("some chunk")
    assert graph.nodes == []


def test_construction_never_eagerly_fails_without_an_api_key():
    AnthropicExtractor(model="claude-sonnet-5", api_key=None)
