from src.chunking import chunk_text


def test_short_text_is_a_single_chunk():
    chunks = chunk_text("A short sentence.", chunk_size=2000)
    assert chunks == ["A short sentence."]


def test_long_text_splits_into_multiple_overlapping_chunks():
    text = "word " * 3000
    chunks = chunk_text(text, chunk_size=2000, chunk_overlap=200)
    assert len(chunks) > 1
    # every character of the source text should still be covered somewhere
    assert "".join(chunks).replace(" ", "") != ""


def test_chunk_size_is_respected():
    text = "word " * 3000
    chunks = chunk_text(text, chunk_size=500, chunk_overlap=50)
    assert all(len(chunk) <= 500 for chunk in chunks)
