"""Builds an Extractor for a chosen provider/model. Keeps provider selection
logic out of the frontends and pipeline.py, which only need the Extractor
protocol.

Dispatches on ProviderConfig.kind rather than on the provider's name, so this
stays correct as soon as providers.py declares a new provider - no second
place to remember to update.
"""

from src.extraction.anthropic_extractor import AnthropicExtractor
from src.extraction.base import Extractor
from src.extraction.openai_compatible import OpenAICompatibleExtractor
from src.extraction.providers import get_providers


def create_extractor(provider: str, model: str) -> Extractor:
    config = get_providers()[provider]
    if config.kind == "anthropic":
        return AnthropicExtractor(model=model, api_key=config.api_key)
    return OpenAICompatibleExtractor(
        model=model,
        base_url=config.base_url,
        api_key=config.api_key,
        tokens_per_minute=config.tokens_per_minute,
    )
