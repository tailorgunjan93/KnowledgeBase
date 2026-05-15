"""AES-256-GCM encryption for sensitive user settings (API keys) stored in the DB.

Usage
-----
    from src.shared.encryption import encrypt, decrypt, is_sensitive

    # On save (POST /auth/settings):
    stored = encrypt(raw_value) if is_sensitive(key) else raw_value

    # On load (factory / internal use):
    raw = decrypt(stored_value)

    # On GET /auth/settings (frontend display):
    display = SENTINEL if (is_sensitive(key) and stored_value) else stored_value

Backward compatibility
----------------------
Values that don't start with the "enc:" prefix are treated as legacy plaintext
and returned as-is.  They get re-encrypted the next time the user saves them.

Key setup
---------
Set ENCRYPTION_KEY in .env to a 64-char hex string (32 bytes):
    python -c "import secrets; print(secrets.token_hex(32))"

If the key is missing, a random one is generated at startup — keys will NOT
survive restarts.  Always set a real key in production.
"""

import os
import base64
import secrets
import logging
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

logger = logging.getLogger(__name__)

# ── Sentinel returned to the frontend instead of the real (decrypted) value ──
SENTINEL = "__set__"

# ── Keys whose values are encrypted at rest ──────────────────────────────────
SENSITIVE_KEYS: frozenset[str] = frozenset({
    "groq_api_key",
    "openai_api_key",
    "gemini_api_key",
    "nvidia_api_key",
    "aws_secret_access_key",
    "serper_api_key",
})

_ENC_PREFIX = "enc:"
_cached_key: bytes | None = None


def _load_key() -> bytes:
    """Return the 32-byte AES key, loading from ENCRYPTION_KEY env var."""
    global _cached_key
    if _cached_key is not None:
        return _cached_key

    raw = os.environ.get("ENCRYPTION_KEY", "").strip()
    if len(raw) == 64:
        try:
            _cached_key = bytes.fromhex(raw)
            logger.info("Encryption key loaded from ENCRYPTION_KEY env var.")
            return _cached_key
        except ValueError:
            pass

    # Auto-generate for dev — loud warning
    logger.warning(
        "\n"
        "  ⚠️  ENCRYPTION_KEY is not set or invalid.\n"
        "  A temporary key has been generated — encrypted data WILL BE LOST on restart.\n"
        "  Add to .env:\n"
        "    ENCRYPTION_KEY=<run: python -c \"import secrets; print(secrets.token_hex(32))\">\n"
    )
    _cached_key = secrets.token_bytes(32)
    return _cached_key


def is_sensitive(key: str) -> bool:
    """Return True if this setting key should be encrypted."""
    return key in SENSITIVE_KEYS


def encrypt(plaintext: str) -> str:
    """Encrypt *plaintext* with AES-256-GCM.

    Returns an ``enc:<base64>`` string.
    Passes through empty strings and already-encrypted values unchanged.
    """
    if not plaintext:
        return plaintext
    if plaintext.startswith(_ENC_PREFIX):
        return plaintext  # already encrypted — idempotent

    key = _load_key()
    nonce = secrets.token_bytes(12)          # 96-bit random nonce (GCM standard)
    ciphertext = AESGCM(key).encrypt(nonce, plaintext.encode("utf-8"), None)
    encoded = base64.urlsafe_b64encode(nonce + ciphertext).decode("ascii")
    return f"{_ENC_PREFIX}{encoded}"


def decrypt(value: str) -> str:
    """Decrypt an ``enc:<base64>`` string back to plaintext.

    Passes through plain-text values (legacy / non-sensitive) unchanged.
    Returns an empty string if decryption fails (e.g. key rotation).
    """
    if not value or not value.startswith(_ENC_PREFIX):
        return value  # legacy plaintext — return as-is

    try:
        raw = base64.urlsafe_b64decode(value[len(_ENC_PREFIX):])
        nonce, ciphertext = raw[:12], raw[12:]
        return AESGCM(_load_key()).decrypt(nonce, ciphertext, None).decode("utf-8")
    except Exception:
        logger.error(
            "Failed to decrypt a stored API key. "
            "The ENCRYPTION_KEY may have changed. "
            "The user will need to re-enter the key."
        )
        return ""
