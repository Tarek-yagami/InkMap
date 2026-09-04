"""Streamlit frontend: upload a document or paste text, view the extracted knowledge graph."""

import asyncio

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

from src.extraction.factory import create_extractor
from src.extraction.providers import PROVIDERS
from src.graph.render import render_html
from src.ingestion import extract_text
from src.pipeline import build_graph

load_dotenv()

st.set_page_config(page_title="InkMap", layout="wide")
st.title("InkMap")
st.caption("Turn a research paper into an interactive map of its entities and relationships.")

uploaded_file = st.file_uploader("Upload a document", type=["pdf", "docx", "pptx"])
pasted_text = st.text_area("...or paste text directly", height=200)

provider = st.selectbox("Provider", list(PROVIDERS.keys()))
if provider == "Ollama (local)":
    model = st.text_input("Model", value=PROVIDERS[provider].models[0])
else:
    model = st.selectbox("Model", PROVIDERS[provider].models)

if st.button("Generate graph", type="primary"):
    text = pasted_text.strip()
    if uploaded_file is not None:
        with st.spinner("Parsing document..."):
            text = extract_text(uploaded_file.getvalue(), uploaded_file.name)

    if not text:
        st.warning("Upload a document or paste some text first.")
    else:
        with st.spinner("Extracting entities and relationships..."):
            try:
                extractor = create_extractor(provider, model)
                graph = asyncio.run(build_graph(text, extractor))
            except Exception as exc:
                st.error(f"Extraction failed: {exc}")
                st.stop()
            html = render_html(graph)

        st.session_state["graph_html"] = html
        st.session_state["node_count"] = len(graph.nodes)
        st.session_state["edge_count"] = len(graph.edges)

if "graph_html" in st.session_state:
    st.success(f"{st.session_state['node_count']} entities, {st.session_state['edge_count']} relationships")
    components.html(st.session_state["graph_html"], height=680, scrolling=True)
    st.download_button(
        "Download interactive HTML",
        data=st.session_state["graph_html"],
        file_name="paper_graph.html",
        mime="text/html",
    )
