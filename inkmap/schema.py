"""Domain models for the extracted knowledge graph."""

from typing import Literal

from pydantic import BaseModel

NodeType = Literal["Technology", "Method", "Concept", "Person", "Organization", "Dataset"]


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
