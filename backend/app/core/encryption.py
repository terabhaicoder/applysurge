"""
AES encryption utilities for securing platform credentials.
Uses Fernet symmetric encryption from the cryptography library.
"""

import base64
import hashlib
import logging
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings

logger = logging.getLogger(__name__)


def _get_fernet_key() -> bytes:
    """
    Derive a valid Fernet key from the configured encryption key.
    Fernet requires a 32-byte URL-safe base64-encoded key.
    We hash the configured key with SHA-256 to ensure consistent length.
    """
    key_bytes = settings.ENCRYPTION_KEY.encode("utf-8")
    hashed = hashlib.sha256(key_bytes).digest()
    return base64.urlsafe_b64encode(hashed)


def get_fernet() -> Fernet:
    """Get a Fernet instance using the application encryption key."""
    return Fernet(_get_fernet_key())


def encrypt_value(plaintext: str) -> str:
    """
    Encrypt a plaintext string using Fernet (AES-128-CBC with HMAC).

    Args:
        plaintext: The string to encrypt.

    Returns:
        Base64-encoded ciphertext string suitable for database storage.
    """
    if not plaintext:
        return ""
    fernet = get_fernet()
    encrypted = fernet.encrypt(plaintext.encode("utf-8"))
    return encrypted.decode("utf-8")


def decrypt_value(ciphertext: str) -> Optional[str]:
    """
    Decrypt a Fernet-encrypted ciphertext string.

    Args:
        ciphertext: The base64-encoded encrypted string.

    Returns:
        Decrypted plaintext string, or None if decryption fails.
    """
    if not ciphertext:
        return None
    try:
        fernet = get_fernet()
        decrypted = fernet.decrypt(ciphertext.encode("utf-8"))
        return decrypted.decode("utf-8")
    except (InvalidToken, Exception) as e:
        logger.warning("Decryption failed for a ciphertext value: %s", e)
        return None


def encrypt_dict(data: dict) -> dict:
    """
    Encrypt all string values in a dictionary.
    Non-string values are left unchanged.

    Args:
        data: Dictionary with values to encrypt.

    Returns:
        New dictionary with encrypted string values.
    """
    encrypted = {}
    for key, value in data.items():
        if isinstance(value, str) and value:
            encrypted[key] = encrypt_value(value)
        else:
            encrypted[key] = value
    return encrypted


def decrypt_dict(data: dict) -> dict:
    """
    Decrypt all string values in a dictionary that appear to be Fernet tokens.
    Non-encrypted values are left unchanged.

    Args:
        data: Dictionary with potentially encrypted values.

    Returns:
        New dictionary with decrypted values.
    """
    decrypted = {}
    for key, value in data.items():
        if isinstance(value, str) and value:
            result = decrypt_value(value)
            decrypted[key] = result if result is not None else value
        else:
            decrypted[key] = value
    return decrypted


def rotate_encryption_key(ciphertext: str, old_key: str, new_key: str) -> Optional[str]:
    """
    Re-encrypt a value with a new encryption key.
    Useful for key rotation.

    Args:
        ciphertext: The currently encrypted value.
        old_key: The old encryption key.
        new_key: The new encryption key.

    Returns:
        Re-encrypted value with the new key, or None on failure.
    """
    try:
        old_key_bytes = hashlib.sha256(old_key.encode("utf-8")).digest()
        old_fernet = Fernet(base64.urlsafe_b64encode(old_key_bytes))

        plaintext = old_fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")

        new_key_bytes = hashlib.sha256(new_key.encode("utf-8")).digest()
        new_fernet = Fernet(base64.urlsafe_b64encode(new_key_bytes))

        return new_fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")
    except (InvalidToken, Exception):
        return None
