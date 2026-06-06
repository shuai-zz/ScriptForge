"""Unit tests for ChatModel factory (Task 4.6)."""

from unittest.mock import MagicMock, patch

import pytest

from app.services.llm_factory import LLMFactoryError, create_chat_model


class TestCreateChatModelAnthropic:
    """Anthropic provider dispatch."""

    @patch("app.services.llm_factory.ChatAnthropic")
    @patch("app.services.llm_factory.decrypt")
    def test_basic_creation(self, mock_decrypt, mock_chat_anthropic):
        mock_decrypt.return_value = "sk-ant-api03-test-key"
        mock_instance = MagicMock()
        mock_chat_anthropic.return_value = mock_instance

        provider = MagicMock()
        provider.provider_type = "anthropic"
        provider.provider_id = "prov-claude"
        provider.model_name = "claude-sonnet-4-6"
        provider.encrypted_api_key = "encrypted-data"
        provider.parameters = {"temperature": 0.7}
        provider.base_url = None

        result = create_chat_model(provider)

        mock_decrypt.assert_called_once_with("encrypted-data")
        mock_chat_anthropic.assert_called_once_with(
            model="claude-sonnet-4-6",
            api_key="sk-ant-api03-test-key",
            temperature=0.7,
        )
        assert result is mock_instance

    @patch("app.services.llm_factory.ChatAnthropic")
    @patch("app.services.llm_factory.decrypt")
    def test_with_base_url(self, mock_decrypt, mock_chat_anthropic):
        mock_decrypt.return_value = "sk-ant-test-key"
        mock_chat_anthropic.return_value = MagicMock()

        provider = MagicMock()
        provider.provider_type = "anthropic"
        provider.provider_id = "prov-claude-proxy"
        provider.model_name = "claude-sonnet-4-6"
        provider.encrypted_api_key = "enc"
        provider.parameters = {"temperature": 0.7}
        provider.base_url = "https://anthropic.proxy.internal"

        create_chat_model(provider)

        mock_chat_anthropic.assert_called_once_with(
            model="claude-sonnet-4-6",
            api_key="sk-ant-test-key",
            temperature=0.7,
            base_url="https://anthropic.proxy.internal",
        )

    @patch("app.services.llm_factory.ChatAnthropic")
    @patch("app.services.llm_factory.decrypt")
    def test_with_max_tokens(self, mock_decrypt, mock_chat_anthropic):
        mock_decrypt.return_value = "sk-ant-api03-test-key"
        mock_chat_anthropic.return_value = MagicMock()

        provider = MagicMock()
        provider.provider_type = "anthropic"
        provider.provider_id = "prov-claude"
        provider.model_name = "claude-sonnet-4-6"
        provider.encrypted_api_key = "enc"
        provider.parameters = {"temperature": 0.5, "max_tokens": 4096}
        provider.base_url = None

        create_chat_model(provider)

        mock_chat_anthropic.assert_called_once_with(
            model="claude-sonnet-4-6",
            api_key="sk-ant-api03-test-key",
            temperature=0.5,
            max_tokens=4096,
        )

    @patch("app.services.llm_factory.ChatAnthropic")
    @patch("app.services.llm_factory.decrypt")
    def test_with_thinking_enabled(self, mock_decrypt, mock_chat_anthropic):
        mock_decrypt.return_value = "sk-ant-api03-test-key"
        mock_chat_anthropic.return_value = MagicMock()

        provider = MagicMock()
        provider.provider_type = "anthropic"
        provider.provider_id = "prov-claude"
        provider.model_name = "claude-sonnet-4-6"
        provider.encrypted_api_key = "enc"
        provider.parameters = {"temperature": 0.7, "thinking": True}
        provider.base_url = None

        create_chat_model(provider)

        mock_chat_anthropic.assert_called_once_with(
            model="claude-sonnet-4-6",
            api_key="sk-ant-api03-test-key",
            temperature=0.7,
            thinking={"type": "enabled", "budget_tokens": 1024},
        )

    @patch("app.services.llm_factory.ChatAnthropic")
    @patch("app.services.llm_factory.decrypt")
    def test_thinking_disabled_not_passed(self, mock_decrypt, mock_chat_anthropic):
        mock_decrypt.return_value = "sk-ant-api03-test-key"
        mock_chat_anthropic.return_value = MagicMock()

        provider = MagicMock()
        provider.provider_type = "anthropic"
        provider.provider_id = "prov-claude"
        provider.model_name = "claude-sonnet-4-6"
        provider.encrypted_api_key = "enc"
        provider.parameters = {"temperature": 0.7, "thinking": False}
        provider.base_url = None

        create_chat_model(provider)

        call_kwargs = mock_chat_anthropic.call_args.kwargs
        assert "thinking" not in call_kwargs


class TestCreateChatModelOpenAICompatible:
    """OpenAI-compatible provider dispatch."""

    @patch("app.services.llm_factory.ChatOpenAI")
    @patch("app.services.llm_factory.decrypt")
    def test_basic_creation(self, mock_decrypt, mock_chat_openai):
        mock_decrypt.return_value = "sk-openai-test-key"
        mock_instance = MagicMock()
        mock_chat_openai.return_value = mock_instance

        provider = MagicMock()
        provider.provider_type = "openai_compatible"
        provider.provider_id = "prov-gpt"
        provider.model_name = "gpt-4o"
        provider.encrypted_api_key = "encrypted-data"
        provider.parameters = {"temperature": 0.7}
        provider.base_url = None

        result = create_chat_model(provider)

        mock_decrypt.assert_called_once_with("encrypted-data")
        mock_chat_openai.assert_called_once_with(
            model="gpt-4o",
            api_key="sk-openai-test-key",
            temperature=0.7,
        )
        assert result is mock_instance

    @patch("app.services.llm_factory.ChatOpenAI")
    @patch("app.services.llm_factory.decrypt")
    def test_with_custom_base_url(self, mock_decrypt, mock_chat_openai):
        mock_decrypt.return_value = "sk-test-key"
        mock_chat_openai.return_value = MagicMock()

        provider = MagicMock()
        provider.provider_type = "openai_compatible"
        provider.provider_id = "prov-custom"
        provider.model_name = "custom-model"
        provider.encrypted_api_key = "enc"
        provider.parameters = {"temperature": 0.3}
        provider.base_url = "https://api.custom.com/v1"

        create_chat_model(provider)

        mock_chat_openai.assert_called_once_with(
            model="custom-model",
            api_key="sk-test-key",
            temperature=0.3,
            base_url="https://api.custom.com/v1",
        )

    @patch("app.services.llm_factory.ChatOpenAI")
    @patch("app.services.llm_factory.decrypt")
    def test_with_max_tokens(self, mock_decrypt, mock_chat_openai):
        mock_decrypt.return_value = "sk-test-key"
        mock_chat_openai.return_value = MagicMock()

        provider = MagicMock()
        provider.provider_type = "openai_compatible"
        provider.provider_id = "prov-gpt"
        provider.model_name = "gpt-4o"
        provider.encrypted_api_key = "enc"
        provider.parameters = {"temperature": 0.5, "max_tokens": 2048}
        provider.base_url = None

        create_chat_model(provider)

        mock_chat_openai.assert_called_once_with(
            model="gpt-4o",
            api_key="sk-test-key",
            temperature=0.5,
            max_tokens=2048,
        )


class TestCreateChatModelErrors:
    """Error handling paths."""

    def test_unsupported_provider_type(self):
        provider = MagicMock()
        provider.provider_type = "unknown_provider"
        provider.provider_id = "prov-unknown"
        provider.encrypted_api_key = "enc"

        with pytest.raises(LLMFactoryError) as exc_info:
            create_chat_model(provider)
        assert "unknown_provider" in str(exc_info.value)
        assert "Unsupported provider_type" in str(exc_info.value)

    @patch("app.services.llm_factory.decrypt")
    def test_decrypt_failure_raises_llm_factory_error(self, mock_decrypt):
        mock_decrypt.side_effect = ValueError("Invalid tag")

        provider = MagicMock()
        provider.provider_type = "anthropic"
        provider.provider_id = "prov-claude"
        provider.encrypted_api_key = "bad-encrypted-data"
        provider.parameters = {"temperature": 0.7}
        provider.model_name = "claude-sonnet-4-6"
        provider.base_url = None

        with pytest.raises(LLMFactoryError) as exc_info:
            create_chat_model(provider)
        assert "Failed to decrypt API key" in str(exc_info.value)
        assert "prov-claude" in str(exc_info.value)
