"""ChatModel factory — unified interface for multiple LLM providers."""

from typing import Literal

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel

from app.core.encryption import decrypt
from app.models.conversion import LLMProvider


class LLMFactoryError(Exception):
    """Raised when provider configuration is invalid or unsupported."""

    pass


def create_chat_model(provider: LLMProvider) -> BaseChatModel:
    """Create a LangChain ChatModel from an LLMProvider database record.

    Args:
        provider: An LLMProvider ORM instance with encrypted_api_key.

    Returns:
        A configured BaseChatModel (ChatAnthropic or ChatOpenAI).

    Raises:
        LLMFactoryError: If provider_type is unsupported or config is invalid.
    """
    # Decrypt the API key for runtime use
    try:
        api_key = decrypt(provider.encrypted_api_key)
    except Exception as exc:
        raise LLMFactoryError(f"Failed to decrypt API key for provider {provider.provider_id}") from exc

    params = provider.parameters or {}
    temperature = params.get("temperature", 0.7)
    max_tokens = params.get("max_tokens")

    if provider.provider_type == "anthropic":
        kwargs: dict = {
            "model": provider.model_name,
            "api_key": api_key,
            "temperature": temperature,
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        if params.get("thinking"):
            kwargs["thinking"] = {"type": "enabled", "budget_tokens": 1024}
        return ChatAnthropic(**kwargs)

    elif provider.provider_type == "openai_compatible":
        kwargs = {
            "model": provider.model_name,
            "api_key": api_key,
            "temperature": temperature,
        }
        if provider.base_url:
            kwargs["base_url"] = provider.base_url
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        return ChatOpenAI(**kwargs)

    else:
        raise LLMFactoryError(
            f"Unsupported provider_type: {provider.provider_type}. "
            "Expected 'anthropic' or 'openai_compatible'."
        )
