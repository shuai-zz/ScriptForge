"""Unit tests for AES-256-GCM API key encryption utility (Task 3.9)."""

import base64

import pytest
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.encryption import decrypt, encrypt, mask_key


class TestEncryptDecryptRoundtrip:
    """Encryption and decryption must be symmetric."""

    def test_roundtrip_with_standard_key(self):
        plaintext = "sk-ant-api03-demo-key-12345"
        ciphertext = encrypt(plaintext)
        decrypted = decrypt(ciphertext)
        assert decrypted == plaintext

    def test_roundtrip_with_unicode(self):
        plaintext = "中文密钥测试-12345"
        ciphertext = encrypt(plaintext)
        decrypted = decrypt(ciphertext)
        assert decrypted == plaintext

    def test_roundtrip_with_special_chars(self):
        plaintext = "key-with_underscore.and+dash=equals"
        ciphertext = encrypt(plaintext)
        decrypted = decrypt(ciphertext)
        assert decrypted == plaintext

    def test_ciphertext_is_deterministically_different(self):
        """Same plaintext encrypted twice should yield different ciphertexts (nonce randomness)."""
        plaintext = "same-text"
        ciphertext1 = encrypt(plaintext)
        ciphertext2 = encrypt(plaintext)
        assert ciphertext1 != ciphertext2
        # But both decrypt to the same plaintext
        assert decrypt(ciphertext1) == plaintext
        assert decrypt(ciphertext2) == plaintext


class TestMaskKey:
    """Key masking for safe display."""

    def test_standard_openai_key(self):
        assert mask_key("sk-abc1234567890xyz") == "sk-***...***xyz"

    def test_anthropic_key(self):
        assert mask_key("sk-ant-api03-long-key-value") == "sk-***...***lue"

    def test_deepseek_key(self):
        assert mask_key("sk-ds9abcdef") == "sk-***...***def"

    def test_short_key(self):
        """Very short keys should still be masked."""
        assert mask_key("sk-abc") == "***"

    def test_no_prefix(self):
        """Keys without known prefix are masked from the start."""
        assert mask_key("plainkeyvalue123") == "sk-***...***123"

    def test_exactly_six_chars(self):
        """Boundary: 6 chars body -> fully hidden."""
        assert mask_key("sk-abcdef") == "***"


class TestTamperedCiphertext:
    """Tampered or malformed ciphertext must raise an error."""

    def test_tampered_ciphertext(self):
        plaintext = "secret-key"
        ciphertext = encrypt(plaintext)
        # Flip one bit in the base64-decoded payload
        raw = bytearray(base64.b64decode(ciphertext))
        raw[-1] ^= 0xFF  # flip last byte
        tampered = base64.b64encode(raw).decode("ascii")

        with pytest.raises(ValueError):
            decrypt(tampered)

    def test_truncated_ciphertext(self):
        """Missing auth tag bytes."""
        plaintext = "secret-key"
        ciphertext = encrypt(plaintext)
        raw = base64.b64decode(ciphertext)
        truncated = base64.b64encode(raw[:-5]).decode("ascii")

        with pytest.raises(ValueError):
            decrypt(truncated)

    def test_invalid_base64(self):
        with pytest.raises(Exception):  # base64 decode error
            decrypt("not-valid-base64!!!")

    def test_empty_string(self):
        with pytest.raises(Exception):
            decrypt("")

    def test_wrong_nonce_size(self):
        """Nonce is 12 bytes; tamper with nonce size."""
        plaintext = "secret-key"
        ciphertext = encrypt(plaintext)
        raw = bytearray(base64.b64decode(ciphertext))
        # prepend extra bytes to nonce
        tampered = base64.b64encode(bytes([0, 0]) + raw).decode("ascii")

        with pytest.raises(ValueError):
            decrypt(tampered)
