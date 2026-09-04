"""Request/response shape tests via FastAPI's TestClient. The SSE stream
itself isn't covered here (awkward to unit test); that's what the manual
`curl -N` pass during development is for. The background job task always
runs against a mocked extractor so these tests never touch the network or
need a real API key, which matters for CI running with no secrets set.
"""

import time

from fastapi.testclient import TestClient

from backend.main import app
from src.schema import Edge, KnowledgeGraph, Node

client = TestClient(app)


class FakeExtractor:
    async def extract(self, chunk: str) -> KnowledgeGraph:
        return KnowledgeGraph(
            nodes=[Node(name="Transformer", type="Technology")],
            edges=[Edge(source="Transformer", target="Transformer", relationship="self")],
        )


def test_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_providers_never_exposes_api_key():
    resp = client.get("/api/providers")
    assert resp.status_code == 200
    assert "api_key" not in resp.text
    names = {p["name"] for p in resp.json()}
    assert names == {"OpenAI", "Groq", "Ollama (local)"}


def test_hidden_providers_env_var_filters_the_list(monkeypatch):
    monkeypatch.setenv("INKMAP_HIDDEN_PROVIDERS", "Ollama (local)")
    resp = client.get("/api/providers")
    names = {p["name"] for p in resp.json()}
    assert "Ollama (local)" not in names
    assert "Groq" in names


def test_start_job_requires_text_or_file():
    resp = client.post("/api/jobs", data={"provider": "Groq", "model": "openai/gpt-oss-120b"})
    assert resp.status_code == 400


def test_start_job_returns_a_job_id_and_completes(monkeypatch):
    monkeypatch.setattr("backend.jobs.runner.create_extractor", lambda provider, model: FakeExtractor())

    resp = client.post(
        "/api/jobs", data={"text": "some paper text", "provider": "Groq", "model": "openai/gpt-oss-120b"}
    )
    assert resp.status_code == 202
    job_id = resp.json()["job_id"]

    for _ in range(50):
        status = client.get(f"/api/jobs/{job_id}").json()
        if status["status"] != "running":
            break
        time.sleep(0.05)

    assert status["status"] == "complete"
    assert status["result"]["nodes"][0]["name"] == "Transformer"


def test_get_unknown_job_404():
    assert client.get("/api/jobs/does-not-exist").status_code == 404


def test_stream_unknown_job_404():
    assert client.get("/api/jobs/does-not-exist/stream").status_code == 404
