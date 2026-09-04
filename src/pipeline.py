"""Orchestrates chunking, extraction, and merging into one KnowledgeGraph.

Depends on the Extractor protocol, not a concrete provider, so callers choose
which model backs the extraction.
"""

import asyncio
import logging

from src.chunking import chunk_text
from src.extraction.base import Extractor
from src.graph.merge import merge_graphs
from src.schema import KnowledgeGraph

logger = logging.getLogger(__name__)


async def build_graph(text: str, extractor: Extractor) -> KnowledgeGraph:
    chunks = chunk_text(text)
    # A single chunk producing off-schema JSON is expected, ordinary LLM
    # behavior, not a reason to discard every other chunk that succeeded.
    results = await asyncio.gather(*(extractor.extract(chunk) for chunk in chunks), return_exceptions=True)

    graphs = [result for result in results if isinstance(result, KnowledgeGraph)]
    failed_count = len(results) - len(graphs)
    if failed_count:
        logger.warning("%d/%d chunks failed extraction and were skipped", failed_count, len(chunks))
    if not graphs:
        raise RuntimeError("Extraction failed for every chunk; no graph could be built.")

    return merge_graphs(graphs)
