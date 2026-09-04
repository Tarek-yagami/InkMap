import pytest
from pydantic import ValidationError

from src.schema import Edge, KnowledgeGraph, Node


def test_node_accepts_any_type_string():
    # NodeType is a plain str, not a strict Literal, deliberately: an LLM
    # occasionally picks an off-taxonomy label (e.g. "Task" instead of one
    # of the six suggested categories), and that should still be valid data.
    node = Node(name="English constituency parsing", type="Task")
    assert node.type == "Task"


def test_node_requires_name_and_type():
    with pytest.raises(ValidationError):
        Node(name="Transformer")
    with pytest.raises(ValidationError):
        Node(type="Technology")


def test_edge_requires_all_fields():
    edge = Edge(source="Transformer", target="attention mechanism", relationship="based on")
    assert edge.source == "Transformer"
    with pytest.raises(ValidationError):
        Edge(source="Transformer", relationship="based on")


def test_knowledge_graph_round_trips_through_json():
    graph = KnowledgeGraph(
        nodes=[Node(name="Transformer", type="Technology")],
        edges=[Edge(source="Transformer", target="Transformer", relationship="self")],
    )
    restored = KnowledgeGraph.model_validate_json(graph.model_dump_json())
    assert restored == graph
