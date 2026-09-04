"""Orchestrates chunking, extraction, and merging into one KnowledgeGraph.

Depends on the Extractor protocol, not a concrete provider, so callers choose
which model backs the extraction.
"""

import asyncio

from src.chunking import chunk_text
from src.extraction.base import Extractor
from src.graph.merge import merge_graphs
from src.schema import KnowledgeGraph


async def build_graph(text: str, extractor: Extractor) -> KnowledgeGraph:
    chunks = chunk_text(text)
    graphs = await asyncio.gather(*(extractor.extract(chunk) for chunk in chunks))
    return merge_graphs(graphs)
