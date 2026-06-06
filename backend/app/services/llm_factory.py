"""ChatModel factory — unified interface for multiple LLM providers."""

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel

from app.core.encryption import decrypt
from app.models.conversion import LLMProvider


class LLMFactoryError(Exception):
    """Raised when provider configuration is invalid or unsupported."""

    pass


def _validate_provider_type(provider_type: str) -> None:
    if provider_type not in ("anthropic", "openai_compatible"):
        raise LLMFactoryError(
            f"Unsupported provider_type: {provider_type}. "
            "Expected 'anthropic' or 'openai_compatible'."
        )


def _build_kwargs(
    provider_type: str,
    model_name: str,
    api_key: str,
    base_url: str | None,
    parameters: dict | None,
) -> dict:
    """Build kwargs dict for ChatAnthropic or ChatOpenAI."""
    params = parameters or {}
    temperature = params.get("temperature", 0.7)
    max_tokens = params.get("max_tokens")

    if provider_type == "anthropic":
        kwargs: dict = {
            "model": model_name,
            "api_key": api_key,
            "temperature": temperature,
        }
        if base_url:
            kwargs["base_url"] = base_url
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        if params.get("thinking"):
            kwargs["thinking"] = {"type": "enabled", "budget_tokens": 1024}
        return kwargs

    else:  # openai_compatible
        kwargs = {
            "model": model_name,
            "api_key": api_key,
            "temperature": temperature,
        }
        if base_url:
            kwargs["base_url"] = base_url
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        return kwargs


def _instantiate_model(provider_type: str, kwargs: dict) -> BaseChatModel:
    if provider_type == "anthropic":
        return ChatAnthropic(**kwargs)
    return ChatOpenAI(**kwargs)


def create_chat_model(provider: LLMProvider) -> BaseChatModel:
    """Create a LangChain ChatModel from an LLMProvider database record.

    Args:
        provider: An LLMProvider ORM instance with encrypted_api_key.

    Returns:
        A configured BaseChatModel (ChatAnthropic or ChatOpenAI).

    Raises:
        LLMFactoryError: If provider_type is unsupported or config is invalid.
    """
    _validate_provider_type(provider.provider_type)

    try:
        api_key = decrypt(provider.encrypted_api_key)
    except Exception as exc:
        raise LLMFactoryError(
            f"Failed to decrypt API key for provider {provider.provider_id}"
        ) from exc

    kwargs = _build_kwargs(
        provider.provider_type,
        provider.model_name,
        api_key,
        provider.base_url,
        provider.parameters,
    )
    return _instantiate_model(provider.provider_type, kwargs)


def create_chat_model_from_config(config: dict) -> BaseChatModel:
    """Create a ChatModel from a plain dict (api_key is already decrypted).

    Used by LangGraph pipeline nodes where providers are injected via
    RunnableConfig instead of fetched from the database.
    """
    provider_type = config["provider_type"]
    _validate_provider_type(provider_type)

    kwargs = _build_kwargs(
        provider_type,
        config["model_name"],
        config["api_key"],  # plaintext
        config.get("base_url"),
        config.get("parameters"),
    )
    return _instantiate_model(provider_type, kwargs)
