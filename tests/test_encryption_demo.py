from __future__ import annotations

import pytest

from scripts.encryption_demo import decrypt_bytes, encrypt_bytes


def test_aes_gcm_round_trip_preserves_plaintext():
    plaintext = b"Climate dashboard trusted dataset demo"
    encrypted = encrypt_bytes(plaintext, "a-long-demo-passphrase")
    assert encrypted != plaintext
    assert decrypt_bytes(encrypted, "a-long-demo-passphrase") == plaintext


def test_aes_gcm_rejects_wrong_passphrase():
    encrypted = encrypt_bytes(b"source-backed record", "correct-demo-passphrase")
    with pytest.raises(ValueError, match="Authentication failed"):
        decrypt_bytes(encrypted, "incorrect-demo-passphrase")


def test_aes_gcm_rejects_modified_ciphertext():
    encrypted = bytearray(encrypt_bytes(b"source-backed record", "correct-demo-passphrase"))
    encrypted[-1] ^= 1
    with pytest.raises(ValueError, match="Authentication failed"):
        decrypt_bytes(bytes(encrypted), "correct-demo-passphrase")


def test_aes_gcm_rejects_malformed_container():
    with pytest.raises(ValueError, match="not a supported"):
        decrypt_bytes(b"not encrypted", "correct-demo-passphrase")


def test_aes_gcm_rejects_short_passphrase():
    with pytest.raises(ValueError, match="at least 12"):
        encrypt_bytes(b"test", "short")
