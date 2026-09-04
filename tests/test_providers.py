import importlib

from src.extraction import providers as providers_module
from src.extraction.factory import create_extractor
from src.extraction.providers import get_providers


def test_every_provider_has_a_model_list():
    all_providers = get_providers()
    assert set(all_providers) == {"OpenAI", "Groq", "Ollama (local)"}
    for config in all_providers.values():
        assert len(config.models) > 0


def test_env_vars_resolve_at_call_time_not_import_time(monkeypatch):
    # Regression test for a real bug: providers.py used to be a module-level
    # dict that read GROQ_API_KEY via os.environ.get() at import time. app.py
    # imported it before calling load_dotenv(), so the key was always absent
    # at the moment the dict was built, and every Groq request 401'd even
    # with a correct key in .env. get_providers() being a function (called
    # fresh each time, after .env has definitely been loaded) fixes this
    # regardless of import order.
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    importlib.reload(providers_module)  # simulate importing before the env var exists

    monkeypatch.setenv("GROQ_API_KEY", "a-real-key-set-after-import")
    config = providers_module.get_providers()["Groq"]
    assert config.api_key == "a-real-key-set-after-import"


def test_groq_and_ollama_construct_without_any_env_vars_set(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    # Must not raise: both providers use an explicit non-empty fallback
    # rather than relying on the SDK's implicit OPENAI_API_KEY lookup, which
    # exists only for OpenAI's own endpoint.
    create_extractor("Groq", "openai/gpt-oss-120b")
    create_extractor("Ollama (local)", "llama3.1")


def test_groq_never_falls_back_to_a_real_openai_key(monkeypatch):
    # A Groq request must never carry an OpenAI credential to a third-party
    # host, even if OPENAI_API_KEY happens to be set.
    monkeypatch.setenv("OPENAI_API_KEY", "sk-a-real-looking-openai-key")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    extractor = create_extractor("Groq", "openai/gpt-oss-120b")
    assert extractor._client.api_key != "sk-a-real-looking-openai-key"
