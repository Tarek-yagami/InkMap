"""Orchestrates chunking, extraction, and merging into one KnowledgeGraph.

Depends on the Extractor protocol, not a concrete provider, so callers choose
which model backs the extraction.
"""

import asyncio
import logging
from collections.abc import Callable

from src.chunking import chunk_text
from src.extraction.base import Extractor
from src.graph.merge import merge_graphs
from src.schema import KnowledgeGraph

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[int, int], None]


async def build_graph(
    text: str,
    extractor: Extractor,
    on_progress: ProgressCallback | None = None,
) -> KnowledgeGraph:
    chunks = chunk_text(text)
    total = len(chunks)

    async def extract_safely(chunk: str) -> KnowledgeGraph | BaseException:
        # A single chunk producing off-schema JSON is expected, ordinary LLM
        # behavior, not a reason to discard every other chunk that succeeded.
        try:
            return await extractor.extract(chunk)
        except Exception as exc:
            return exc

    results: list[KnowledgeGraph | BaseException] = []
    for coro in asyncio.as_completed([extract_safely(chunk) for chunk in chunks]):
        results.append(await coro)
        if on_progress:
            on_progress(len(results), total)

    graphs = [result for result in results if isinstance(result, KnowledgeGraph)]
    failed_count = len(results) - len(graphs)
    if failed_count:
        logger.warning("%d/%d chunks failed extraction and were skipped", failed_count, total)
    if not graphs:
        raise RuntimeError("Extraction failed for every chunk; no graph could be built.")

    return merge_graphs(graphs)
