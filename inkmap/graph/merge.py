"""Pure domain logic: merges per-chunk KnowledgeGraphs into one deduplicated graph.
No I/O, so it's fully unit-testable without a network call or an API key."""

from inkmap.schema import Edge, KnowledgeGraph, Node


def merge_graphs(graphs: list[KnowledgeGraph]) -> KnowledgeGraph:
    nodes_by_key: dict[str, Node] = {}
    for graph in graphs:
        for node in graph.nodes:
            key = node.name.strip().lower()
            if key not in nodes_by_key:
                nodes_by_key[key] = node

    edges_by_key: dict[tuple[str, str, str], Edge] = {}
    for graph in graphs:
        for edge in graph.edges:
            source_key = edge.source.strip().lower()
            target_key = edge.target.strip().lower()
            if source_key not in nodes_by_key or target_key not in nodes_by_key:
                continue
            canonical_edge = Edge(
                source=nodes_by_key[source_key].name,
                target=nodes_by_key[target_key].name,
                relationship=edge.relationship,
            )
            key = (source_key, target_key, edge.relationship.strip().lower())
            edges_by_key.setdefault(key, canonical_edge)

    return KnowledgeGraph(nodes=list(nodes_by_key.values()), edges=list(edges_by_key.values()))
