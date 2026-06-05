"""Token counting and context window estimation utilities.

Uses tiktoken for OpenAI-compatible models and character-based
heuristics for Anthropic models.
"""

import re

import tiktoken

# Approximate context window sizes by model family.
CONTEXT_WINDOWS: dict[str, int] = {
    # Anthropic
    "claude-sonnet-4": 200_000,
    "claude-opus-4": 200_000,
    "claude-haiku-4": 200_000,
    # OpenAI
    "gpt-4o": 128_000,
    "gpt-4o-mini": 128_000,
    "gpt-4-turbo": 128_000,
    "gpt-4": 8_192,
    # DeepSeek
    "deepseek-chat": 64_000,
    "deepseek-reasoner": 64_000,
    # Default fallback
    "default": 128_000,
}

# Lazy-loaded tiktoken encoder (avoids network download at import time).
_tiktoken_encoder = None


def _get_tiktoken_encoder():
    global _tiktoken_encoder
    if _tiktoken_encoder is None:
        try:
            _tiktoken_encoder = tiktoken.get_encoding("cl100k_base")
        except Exception:
            _tiktoken_encoder = None
    return _tiktoken_encoder


def count_tokens(text: str, provider_type: str = "openai_compatible") -> int:
    """Estimate token count for a given text.

    For OpenAI-compatible models uses tiktoken (cl100k_base) if available.
    For Anthropic models uses character heuristic (~3.5 chars/token for mixed CN/EN).
    Falls back to heuristic if tiktoken is unavailable.
    """
    if not text:
        return 0

    if provider_type == "anthropic":
        return _estimate_anthropic_tokens(text)

    # OpenAI-compatible: use tiktoken if available
    encoder = _get_tiktoken_encoder()
    if encoder is not None:
        return len(encoder.encode(text))

    # Fallback to heuristic
    return _estimate_anthropic_tokens(text)


def _estimate_anthropic_tokens(text: str) -> int:
    """Heuristic token estimation for Anthropic models.

    Claude tokenizes roughly:
    - English: ~4 chars/token
    - Chinese: ~1.5 chars/token
    - Mixed: we weight by detected script ratio
    """
    if not text:
        return 0

    cn_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
    total_chars = len(text)
    en_chars = total_chars - cn_chars

    # Weighted average
    cn_tokens = cn_chars / 1.5
    en_tokens = en_chars / 4.0
    return int(cn_tokens + en_tokens)


def get_context_window(model_name: str) -> int:
    """Return the context window size for a given model name.

    Falls back to default if model is unknown.
    """
    model_lower = model_name.lower()
    for key, size in CONTEXT_WINDOWS.items():
        if key in model_lower:
            return size
    return CONTEXT_WINDOWS["default"]


def estimate_window_usage(
    text: str,
    model_name: str,
    provider_type: str = "openai_compatible",
) -> dict:
    """Estimate how much of a model's context window a text consumes.

    Returns:
        {
            "token_count": int,
            "context_window": int,
            "usage_percent": float,  # 0.0 - 100.0
            "remaining_tokens": int,
        }
    """
    tokens = count_tokens(text, provider_type)
    window = get_context_window(model_name)
    usage = (tokens / window) * 100.0 if window > 0 else 0.0
    remaining = max(0, window - tokens)

    return {
        "token_count": tokens,
        "context_window": window,
        "usage_percent": round(usage, 2),
        "remaining_tokens": remaining,
    }
