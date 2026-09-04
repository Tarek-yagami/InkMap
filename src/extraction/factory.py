"""Builds an Extractor for a chosen provider/model. Keeps provider selection
logic out of app.py and pipeline.py, which only need the Extractor protocol."""

from src.extraction.base import Extractor
from src.extraction.openai_compatible import OpenAICompatibleExtractor
from src.extraction.providers import get_providers


def create_extractor(provider: str, model: str) -> Extractor:
    config = get_providers()[provider]
    return OpenAICompatibleExtractor(model=model, base_url=config.base_url, api_key=config.api_key)
