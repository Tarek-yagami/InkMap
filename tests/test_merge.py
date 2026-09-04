from src.graph.merge import _is_alias, merge_graphs, resolve_aliases
from src.schema import Edge, KnowledgeGraph, Node


def test_merge_dedupes_nodes_case_insensitively():
    g1 = KnowledgeGraph(nodes=[Node(name="Transformer", type="Technology")], edges=[])
    g2 = KnowledgeGraph(nodes=[Node(name="transformer", type="Technology")], edges=[])
    merged = merge_graphs([g1, g2])
    assert [n.name for n in merged.nodes] == ["Transformer"]


def test_merge_rewrites_edges_to_the_canonical_node_name():
    # Two chunks refer to the same node with different casing; an edge from
    # the second chunk must still resolve to the first chunk's canonical name.
    g1 = KnowledgeGraph(
        nodes=[Node(name="Transformer", type="Technology"), Node(name="BERT", type="Technology")],
        edges=[],
    )
    g2 = KnowledgeGraph(
        nodes=[Node(name="transformer", type="Technology")],
        edges=[Edge(source="BERT", target="transformer", relationship="is based on")],
    )
    merged = merge_graphs([g1, g2])
    assert (merged.edges[0].source, merged.edges[0].target) == ("BERT", "Transformer")


def test_merge_drops_edges_to_unknown_nodes():
    g = KnowledgeGraph(
        nodes=[Node(name="Transformer", type="Technology")],
        edges=[Edge(source="Transformer", target="Nonexistent", relationship="uses")],
    )
    merged = merge_graphs([g])
    assert merged.edges == []


class TestIsAlias:
    """Calibrated against real duplicate-entity data from a live extraction
    run, and against a generic sentence-embedding baseline that failed:
    'Noam'/'Noam Shazeer' scored 0.64 similarity, but unrelated ML terms
    like 'encoder'/'decoder' (0.70) scored higher, so no similarity
    threshold could separate real aliases from merely-related concepts.
    This lexical heuristic is what replaced it.
    """

    def test_first_name_inside_full_name(self):
        assert _is_alias("Noam", "Noam Shazeer")
        assert _is_alias("Ashish", "Ashish Vaswani")

    def test_simple_pluralization(self):
        assert _is_alias("GPU", "GPUs")

    def test_acronym_matches_initials_of_significant_words(self):
        assert _is_alias("BERT", "Bidirectional Encoder Representations from Transformers")

    def test_unrelated_ml_terms_are_not_aliases(self):
        assert not _is_alias("encoder", "decoder")
        assert not _is_alias("self-attention", "multi-head attention")
        assert not _is_alias("recurrence", "convolutions")

    def test_short_acronym_does_not_falsely_substring_match(self):
        # A naive substring check would wrongly match "AI" inside "domain".
        assert not _is_alias("AI", "domain")
        assert not _is_alias("GPU", "group")


def test_resolve_aliases_collapses_duplicates_but_not_distinct_concepts():
    graph = KnowledgeGraph(
        nodes=[
            Node(name="Ashish Vaswani", type="Person"),
            Node(name="Ashish", type="Person"),
            Node(name="Transformer", type="Technology"),
            Node(name="encoder", type="Concept"),
            Node(name="decoder", type="Concept"),
        ],
        edges=[Edge(source="Ashish", target="Transformer", relationship="designed and implemented")],
    )
    resolved = resolve_aliases(graph)
    names = {n.name for n in resolved.nodes}
    assert names == {"Ashish Vaswani", "Transformer", "encoder", "decoder"}
    assert (resolved.edges[0].source, resolved.edges[0].target) == ("Ashish Vaswani", "Transformer")


def test_resolve_aliases_drops_self_loops_between_two_aliases():
    graph = KnowledgeGraph(
        nodes=[Node(name="Ashish Vaswani", type="Person"), Node(name="Ashish", type="Person")],
        edges=[Edge(source="Ashish", target="Ashish Vaswani", relationship="same person as")],
    )
    resolved = resolve_aliases(graph)
    assert resolved.edges == []
