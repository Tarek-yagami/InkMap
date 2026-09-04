"""Streamlit frontend: upload a document or paste text, view the extracted knowledge graph."""

import asyncio

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

from src.extraction.factory import create_extractor
from src.extraction.providers import get_providers
from src.graph.render import render_html
from src.ingestion import extract_text
from src.pipeline import build_graph

load_dotenv()

st.set_page_config(page_title="InkMap", page_icon="🖋️", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
    #MainMenu, footer, [data-testid="stToolbar"] { visibility: hidden; }

    .inkmap-eyebrow {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.75rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #7ea6d6;
        margin-bottom: 0.25rem;
    }
    .inkmap-title { font-size: 2.1rem; font-weight: 700; margin: 0 0 0.35rem 0; }
    .inkmap-subtitle { font-size: 0.95rem; color: #9aa0ac; margin: 0 0 1.25rem 0; max-width: 640px; }
    [data-testid="stMetricValue"] { font-family: 'IBM Plex Mono', monospace; }
    </style>
    <p class="inkmap-eyebrow">InkMap</p>
    <p class="inkmap-title">Paper to knowledge graph</p>
    <p class="inkmap-subtitle">Upload a research paper or paste its text, and InkMap extracts the
    technologies, methods, people, and relationships it discusses into an interactive graph you can explore.</p>
    """,
    unsafe_allow_html=True,
)

providers = get_providers()

with st.container(border=True):
    uploaded_file = st.file_uploader("Upload a document", type=["pdf", "docx", "pptx"])
    pasted_text = st.text_area("...or paste text directly", height=160)

    col_provider, col_model = st.columns(2)
    with col_provider:
        provider = st.selectbox("Provider", list(providers.keys()))
    with col_model:
        if provider == "Ollama (local)":
            model = st.text_input("Model", value=providers[provider].models[0])
        else:
            model = st.selectbox("Model", providers[provider].models)

    generate = st.button("Generate graph", type="primary", use_container_width=True)

if generate:
    text = pasted_text.strip()
    if uploaded_file is not None:
        with st.spinner("Parsing document..."):
            text = extract_text(uploaded_file.getvalue(), uploaded_file.name)

    if not text:
        st.warning("Upload a document or paste some text first.")
    else:
        progress_bar = st.progress(0.0, text="Extracting entities and relationships...")

        def report_progress(done: int, total: int) -> None:
            progress_bar.progress(done / total, text=f"Extracting entities and relationships... ({done}/{total} chunks)")

        try:
            extractor = create_extractor(provider, model)
            graph = asyncio.run(build_graph(text, extractor, on_progress=report_progress))
        except Exception as exc:
            progress_bar.empty()
            st.error(f"Extraction failed: {exc}")
            st.stop()

        progress_bar.empty()
        html = render_html(graph)

        st.session_state["graph_html"] = html
        st.session_state["node_count"] = len(graph.nodes)
        st.session_state["edge_count"] = len(graph.edges)

if "graph_html" in st.session_state:
    stat_a, stat_b = st.columns(2)
    stat_a.metric("Entities", st.session_state["node_count"])
    stat_b.metric("Relationships", st.session_state["edge_count"])

    with st.container(border=True):
        components.html(st.session_state["graph_html"], height=640, scrolling=False)

    st.download_button(
        "Download interactive HTML",
        data=st.session_state["graph_html"],
        file_name="paper_graph.html",
        mime="text/html",
    )
