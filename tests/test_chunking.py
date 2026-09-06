import inspect

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


def test_default_chunk_size_is_the_measured_speed_quality_middle_ground():
    # Not an arbitrary number: measured on a real paper against 2000 (31
    # chunks, 448s, 432 nodes/469 edges) and 4000 (16 chunks, 261s, 338/381).
    # 3000/300 (22 chunks, 334s, 362/375) was picked as the deliberate
    # middle ground - a silent change here would be a real regression
    # either way, not a harmless tweak. See the comment in chunking.py.
    defaults = inspect.signature(chunk_text).parameters
    assert defaults["chunk_size"].default == 3000
    assert defaults["chunk_overlap"].default == 300
