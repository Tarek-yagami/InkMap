"""Renders a KnowledgeGraph as an interactive, dark-mode PyVis network."""

from pyvis.network import Network

from src.schema import KnowledgeGraph

_NODE_COLORS = {
    "Technology": "#4cc9f0",
    "Method": "#f72585",
    "Concept": "#9d4edd",
    "Person": "#ffd166",
    "Organization": "#06d6a0",
    "Dataset": "#ef476f",
}
_DEFAULT_COLOR = "#adb5bd"


def build_network(graph: KnowledgeGraph) -> Network:
    net = Network(height="650px", width="100%", bgcolor="#0d1117", font_color="#e6edf3", directed=True)
    net.barnes_hut(gravity=-3000, central_gravity=0.3, spring_length=120, spring_strength=0.04, damping=0.9)

    for node in graph.nodes:
        net.add_node(
            node.name,
            label=node.name,
            title=node.type,
            color=_NODE_COLORS.get(node.type, _DEFAULT_COLOR),
            shape="dot",
            size=18,
        )

    for edge in graph.edges:
        net.add_edge(edge.source, edge.target, title=edge.relationship, color="#6e7681", arrows="to")

    return net


def render_html(graph: KnowledgeGraph) -> str:
    return build_network(graph).generate_html(notebook=False)
