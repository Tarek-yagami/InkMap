# InkMap

Turns a research paper into an interactive map of its entities and relationships. Upload a PDF (or DOCX/PPTX), or paste text directly, and the app extracts technologies, methods, concepts, people, organizations, and datasets, along with how they relate to each other, then renders the result as a dark-mode, physics-driven network you can pan, zoom, and drag.

## Architecture

```
src/
├── schema.py              # domain model: Node, Edge, KnowledgeGraph
├── chunking.py            # splits text into overlapping chunks, same for every input source
├── ingestion.py           # document -> plain text, via Docling (layout-aware, OCR off)
├── extraction/
│   ├── base.py            # Extractor protocol
│   └── openai_extractor.py # OpenAI structured-output implementation
├── graph/
│   ├── merge.py           # pure, dependency-free graph deduplication/merge logic
│   └── render.py          # PyVis rendering
└── pipeline.py             # orchestrates chunking -> extraction -> merging
app.py                       # Streamlit UI, depends only on the modules above
```

The pipeline depends on the `Extractor` protocol in `extraction/base.py`, not on OpenAI directly. Swapping in a different model provider means adding one new class, not editing the pipeline. Document parsing goes through Docling rather than a bare PDF text extractor, since research papers are usually multi-column and naive extraction scrambles reading order and mangles tables, which directly hurts extraction quality downstream. OCR is disabled since these are digital-native documents, not scans.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
copy .env.example .env      # then fill in OPENAI_API_KEY
```

## Usage

```bash
streamlit run app.py
```

Upload a document or paste text, pick a model, and click "Generate graph."

## Tech stack

Streamlit, OpenAI structured outputs, Pydantic, Docling, PyVis, LangChain text splitters.

## Roadmap

- **Cross-paper knowledge base**: persist extracted graphs across sessions instead of rebuilding one per upload, so entities accumulate into a growing knowledge base rather than a single-paper snapshot.
- **Embedding-based entity resolution**: replace exact lowercase-string matching with similarity matching, so the same entity referenced differently across papers (e.g. "BERT" vs "Bidirectional Encoder Representations from Transformers") collapses into one node.
- **Literature review support**: once entities resolve across papers, surface things like which papers cite or build on the same concepts, and where consensus or disagreement between papers shows up in the graph.
