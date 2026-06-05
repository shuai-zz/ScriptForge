"""AES-256-GCM encryption for API keys at rest.

Uses the SCRIPTFORGE_ENCRYPTION_KEY env var as master key material.
The actual 32-byte AES key is derived via SHA-256.

Ciphertext format: base64(aes_nonce + aes_tag + ciphertext)
"""

import base64
import hashlib
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import settings


_KEY_SIZE = 32
_NONCE_SIZE = 12
_TAG_SIZE = 16


def _derive_key(key_material: str) -> bytes:
    """Derive a 32-byte AES key from arbitrary key material via SHA-256."""
    return hashlib.sha256(key_material.encode("utf-8")).digest()


def _get_aes() -> AESGCM:
    """Build AES-GCM instance from the configured master key."""
    key = _derive_key(settings.SCRIPTFORGE_ENCRYPTION_KEY)
    return AESGCM(key)


def encrypt(plaintext: str) -> str:
    """Encrypt plaintext and return base64-encoded ciphertext.

    Returns a string in the format:
        base64(nonce || tag || ciphertext)
    """
    aes = _get_aes()
    nonce = os.urandom(_NONCE_SIZE)
    ciphertext = aes.encrypt(nonce, plaintext.encode("utf-8"), None)
    # ciphertext includes the auth tag at the end (GCM mode)
    combined = nonce + ciphertext
    return base64.b64encode(combined).decode("ascii")


def decrypt(ciphertext_b64: str) -> str:
    """Decrypt a base64-encoded ciphertext back to plaintext.

    Raises ValueError on tampered or malformed input.
    """
    from cryptography.exceptions import InvalidTag

    aes = _get_aes()
    try:
        combined = base64.b64decode(ciphertext_b64)
        nonce = combined[:_NONCE_SIZE]
        ciphertext = combined[_NONCE_SIZE:]
        plaintext = aes.decrypt(nonce, ciphertext, None)
        return plaintext.decode("utf-8")
    except InvalidTag as exc:
        raise ValueError("ciphertext has been tampered with or is corrupted") from exc


def mask_key(plaintext_key: str) -> str:
    """Mask an API key for display: sk-***...***XyZ

    Shows first 3 chars after prefix and last 3 chars.
    If key doesn't start with a known prefix, uses the whole key.
    """
    # Strip common prefix variations so we mask the key body
    body = plaintext_key
    for prefix in ("sk-ant-", "sk-proj-", "sk-", "sk-"):
        if body.startswith(prefix):
            body = body[len(prefix):]
            break

    if len(body) <= 6:
        return "***"

    return f"sk-***...***{body[-3:]}"
