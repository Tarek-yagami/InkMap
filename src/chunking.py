"""Splits text into overlapping chunks. Used for every input source, so chunking
behavior stays identical whether the text came from a PDF or was pasted directly."""

from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_text(text: str, chunk_size: int = 3000, chunk_overlap: int = 300) -> list[str]:
    # Each chunk costs a fixed per-request token overhead (prompt template +
    # reasoning) regardless of its content size, so fewer/bigger chunks pay
    # that overhead less often for the same document, at a real cost: a
    # denser excerpt gives the model more to track per call, and measured
    # recall drops with it. On a real paper, 2000-char chunks (31 requests,
    # 448s) extracted 432 nodes/469 edges; 4000-char chunks (16 requests,
    # 261s, ~42% faster) only 338/381 - a real ~20% recall loss, not just
    # dedup noise, since both runs go through the same merge step. 3000 is
    # the deliberate middle ground between those two measured points.
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_text(text)
