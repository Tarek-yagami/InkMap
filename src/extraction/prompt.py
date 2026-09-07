"""Extraction task description shared by every Extractor implementation.

What to extract is the same regardless of provider; only how each provider is
told to shape its response differs (a plain JSON-object reply for OpenAI-
compatible APIs, a forced tool call for Anthropic's Messages API), so that part
stays in each extractor module rather than here.
"""

EXTRACTION_TASK = """Extract the key entities and relationships from the following excerpt of a research paper.
Identify technologies, methods, concepts, people, organizations, and datasets as nodes, and describe how they
relate to each other as edges. Only include entities that are explicitly discussed in this excerpt."""
