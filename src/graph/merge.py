"""Pure domain logic: merges per-chunk KnowledgeGraphs into one deduplicated graph.
No I/O, so it's fully unit-testable without a network call or an API key."""

import re

from src.schema import Edge, KnowledgeGraph, Node

_STOPWORDS = {"a", "an", "the", "of", "for", "from", "and", "in", "on", "to"}


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


def _tokens(name: str) -> list[str]:
    return re.findall(r"[A-Za-z']+", name)


def _is_alias(name_a: str, name_b: str) -> bool:
    """True if one name looks like a short form of the other: a first name
    inside a full name ("Noam" / "Noam Shazeer"), a simple plural ("GPU" /
    "GPUs"), or an acronym whose initials spell out the other's significant
    words ("BERT" / "Bidirectional Encoder Representations from Transformers").

    Deliberately narrow and lexical rather than embedding-similarity based:
    tested against general-purpose sentence embeddings first, and generic
    semantic similarity scored unrelated ML terms (e.g. "encoder" / "decoder"
    at 0.70, "self-attention" / "multi-head attention" at 0.67) higher than
    genuine aliases (e.g. "Noam" / "Noam Shazeer" at 0.64), so no threshold
    could separate real aliases from merely-related-but-distinct concepts.
    """
    short, long_ = (name_a, name_b) if len(name_a) <= len(name_b) else (name_b, name_a)
    short_lower = short.lower()
    long_words = [w.lower() for w in _tokens(long_)]

    if any(short_lower == w or short_lower == w.rstrip("s") or short_lower.rstrip("s") == w for w in long_words):
        return True

    if short.isupper() and 2 <= len(short) <= 8:
        significant_words = [w for w in _tokens(long_) if w.lower() not in _STOPWORDS]
        initials = "".join(w[0] for w in significant_words).upper()
        if initials == short.upper():
            return True

    return False


def resolve_aliases(graph: KnowledgeGraph) -> KnowledgeGraph:
    """Collapses alias pairs that exact-match merging misses: different
    mentions of the same entity, like a person's first name next to their
    full name, or an acronym next to its expansion. Runs on already-deduped
    nodes from merge_graphs, since it needs pairwise comparison rather than
    a simple key lookup.
    """
    nodes_longest_first = sorted(graph.nodes, key=lambda node: -len(node.name))
    representatives: list[Node] = []
    canonical_name: dict[str, str] = {}

    for node in nodes_longest_first:
        match = next((rep for rep in representatives if _is_alias(node.name, rep.name)), None)
        if match is None:
            representatives.append(node)
            canonical_name[node.name] = node.name
        else:
            canonical_name[node.name] = match.name

    edges_by_key: dict[tuple[str, str, str], Edge] = {}
    for edge in graph.edges:
        source = canonical_name.get(edge.source, edge.source)
        target = canonical_name.get(edge.target, edge.target)
        if source.lower() == target.lower():
            continue  # was an edge between two aliases of the same entity
        key = (source.lower(), target.lower(), edge.relationship.strip().lower())
        edges_by_key.setdefault(key, Edge(source=source, target=target, relationship=edge.relationship))

    return KnowledgeGraph(nodes=representatives, edges=list(edges_by_key.values()))
