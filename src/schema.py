"""Domain models for the extracted knowledge graph."""

from pydantic import BaseModel

# The extraction prompt asks for one of a fixed set of categories, but an LLM
# occasionally picks a close synonym instead (e.g. "Tool" for "Technology").
# Rejecting the whole node over that would throw away otherwise-valid data;
# render.py already falls back to a default color for any type it doesn't
# recognize, so a plain string is the actual constraint here, not an enum.
NodeType = str


class Node(BaseModel):
    name: str
    type: NodeType


class Edge(BaseModel):
    source: str
    target: str
    relationship: str


class KnowledgeGraph(BaseModel):
    nodes: list[Node]
    edges: list[Edge]
