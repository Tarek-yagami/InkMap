import pytest

from src.pipeline import build_graph
from src.schema import KnowledgeGraph, Node


class MockExtractor:
    def __init__(self, node_name_fn):
        self.calls = 0
        self._node_name_fn = node_name_fn

    async def extract(self, chunk: str) -> KnowledgeGraph:
        self.calls += 1
        return KnowledgeGraph(nodes=[Node(name=self._node_name_fn(self.calls), type="Concept")], edges=[])


class FlakyExtractor:
    def __init__(self, fail_every: int):
        self.calls = 0
        self._fail_every = fail_every

    async def extract(self, chunk: str) -> KnowledgeGraph:
        self.calls += 1
        if self.calls % self._fail_every == 0:
            raise ValueError("simulated malformed JSON from one chunk")
        return KnowledgeGraph(nodes=[Node(name=f"N{self.calls}", type="Concept")], edges=[])


class AlwaysFailExtractor:
    async def extract(self, chunk: str) -> KnowledgeGraph:
        raise ValueError("always fails")


async def test_build_graph_merges_results_across_chunks():
    text = "word " * 3000
    graph = await build_graph(text, MockExtractor(lambda n: f"UniqueNode{n}"))
    assert len(graph.nodes) > 1


async def test_progress_callback_fires_once_per_chunk_in_order():
    calls = []
    text = "word " * 3000
    await build_graph(text, MockExtractor(str), on_progress=lambda done, total: calls.append((done, total)))

    totals = {total for _, total in calls}
    assert len(totals) == 1
    total = totals.pop()
    assert [done for done, _ in calls] == list(range(1, total + 1))


async def test_one_bad_chunk_does_not_discard_the_rest():
    text = "word " * 3000
    graph = await build_graph(text, FlakyExtractor(fail_every=3))
    assert len(graph.nodes) > 0


async def test_progress_still_reaches_total_even_with_failures():
    calls = []
    text = "word " * 3000
    await build_graph(
        text, FlakyExtractor(fail_every=3), on_progress=lambda done, total: calls.append((done, total))
    )
    last_done, last_total = calls[-1]
    assert last_done == last_total


async def test_all_chunks_failing_raises_clearly():
    with pytest.raises(RuntimeError, match="Extraction failed for every chunk"):
        await build_graph("word " * 3000, AlwaysFailExtractor())
