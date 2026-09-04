# InkMap

Turns a research paper into an interactive map of its entities and relationships. Upload a PDF (or DOCX/PPTX), or paste text directly, and the app extracts technologies, methods, concepts, people, organizations, and datasets, along with how they relate to each other, then renders the result as "Ink Bloom": a physics-driven network with glowing category halos and hover-revealed labels, in either dark or light.

## Architecture

```
src/
├── schema.py              # domain model: Node, Edge, KnowledgeGraph
├── chunking.py            # splits text into overlapping chunks, same for every input source
├── ingestion.py           # document -> plain text, via Docling (layout-aware, OCR off)
├── extraction/
│   ├── base.py               # Extractor protocol
│   ├── openai_compatible.py  # one Extractor implementation for any OpenAI-compatible API
│   ├── providers.py          # provider presets (OpenAI, Groq, Ollama): base_url, api_key, models
│   └── factory.py            # builds an Extractor from a chosen provider/model
├── graph/
│   ├── merge.py           # exact-match dedup, then lexical alias resolution ("Noam" -> "Noam Shazeer")
│   └── render.py          # "Ink Bloom" D3 renderer: glowing halos, curved edges, dark/light toggle
└── pipeline.py             # orchestrates chunking -> extraction -> merging
app.py                       # Streamlit UI, depends only on the modules above
.streamlit/config.toml       # Streamlit's native theme config (colors), not CSS overrides
```

The pipeline depends on the `Extractor` protocol in `extraction/base.py`, not on any specific provider. OpenAI, Groq, and local Ollama models all speak the same OpenAI-compatible chat completions API, so one `OpenAICompatibleExtractor` class handles all three; `providers.py` just points it at a different `base_url`/`api_key`. Adding another OpenAI-compatible provider (OpenRouter, Together, ...) means adding one entry to `providers.py`, not a new class. Document parsing goes through Docling rather than a bare PDF text extractor, since research papers are usually multi-column and naive extraction scrambles reading order and mangles tables, which directly hurts extraction quality downstream. OCR is disabled since these are digital-native documents, not scans.

## Setup

With [uv](https://docs.astral.sh/uv/) (recommended, much faster):

```bash
uv sync
copy .env.example .env      # then fill in the key(s) for whichever provider(s) you'll use
```

Without uv, plain pip works too, reading the same `pyproject.toml`:

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install .
copy .env.example .env
```

For Ollama, no API key is needed, just [Ollama](https://ollama.com) running locally with a model pulled (e.g. `ollama pull llama3.1`).

## Usage

```bash
uv run streamlit run app.py     # or: streamlit run app.py, if installed with pip
```

Upload a document or paste text, pick a provider and model, and click "Generate graph."

## Testing

```bash
uv run pytest
```

Covers the pure and mockable logic: chunking, merge/alias resolution, pipeline orchestration (progress reporting, partial-chunk-failure tolerance), provider config, the extractor, and the renderer's HTML output. Docling ingestion isn't covered yet since it needs a bundled PDF fixture and a much slower test run; that's a reasonable next addition, not an oversight.

## Tech stack

Streamlit, OpenAI-compatible structured extraction (OpenAI, Groq, Ollama), Pydantic, Docling, D3.js, LangChain text splitters.

## Roadmap

- **Cross-paper knowledge base**: persist extracted graphs across sessions instead of rebuilding one per upload, so entities accumulate into a growing knowledge base rather than a single-paper snapshot.
- **Literature review support**: once entities resolve across papers, surface things like which papers cite or build on the same concepts, and where consensus or disagreement between papers shows up in the graph.

Within-paper entity resolution (collapsing "Noam" and "Noam Shazeer" into one node) is already handled by `resolve_aliases` in `merge.py`. General-purpose embedding similarity was tried first and rejected: it scored unrelated ML terms like "encoder"/"decoder" higher than genuine aliases, so no threshold could separate them safely. The lexical heuristic that replaced it (substring, pluralization, acronym-initials matching) is scoped to one paper's already-merged nodes; resolving aliases *across* papers is a harder problem tied to the cross-paper knowledge base above.
