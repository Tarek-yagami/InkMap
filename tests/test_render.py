from src.graph.render import render_html
from src.schema import Edge, KnowledgeGraph, Node


def test_render_html_embeds_node_and_edge_data():
    graph = KnowledgeGraph(
        nodes=[Node(name="Transformer", type="Technology"), Node(name="attention mechanism", type="Concept")],
        edges=[Edge(source="Transformer", target="attention mechanism", relationship="based on")],
    )
    html = render_html(graph)
    assert "Transformer" in html
    assert "d3.min.js" in html
    assert "btn-dark" in html and "btn-light" in html


def test_render_html_escapes_embedded_script_close_tags():
    # A node name or relationship containing the literal substring
    # "</script>" would otherwise prematurely close the embedding tag.
    graph = KnowledgeGraph(
        nodes=[Node(name="A", type="Concept"), Node(name="B", type="Concept")],
        edges=[Edge(source="A", target="B", relationship="mentions </script><script>alert(1)")],
    )
    html = render_html(graph)
    assert "</script><script>alert" not in html
