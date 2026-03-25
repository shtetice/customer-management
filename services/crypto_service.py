"""
Basic symmetric encryption for storing sensitive settings (e.g. backup password).

Uses Fernet (AES-128-CBC + HMAC-SHA256) from the `cryptography` package, which is
already a dependency of bcrypt and requires no new installs.

The encryption key is derived from a fixed app secret + a per-installation salt
that is generated once and stored alongside the encrypted value in settings.json.
This means:
  - The value is unreadable without both the source code AND the salt file.
  - Moving settings.json to another machine will not decrypt correctly.
  - It is NOT a substitute for OS-level secret stores, but is far better than
    plain text for protecting accidental exposure (shoulder-surfing, accidental
    git commit, etc.).
"""

import base64
import hashlib
import os

from cryptography.fernet import Fernet, InvalidToken

# Fixed per-app secret — combined with a random salt to derive the Fernet key.
# Changing this constant will invalidate all previously encrypted values.
_APP_SECRET = b"CustomerMgmt-v1-secret-key-do-not-change"


def _derive_key(salt: bytes) -> bytes:
    """Derive a 32-byte key from the app secret + salt, then base64url-encode it."""
    raw = hashlib.pbkdf2_hmac("sha256", _APP_SECRET, salt, iterations=100_000)
    return base64.urlsafe_b64encode(raw)


def encrypt(plaintext: str) -> tuple[str, str]:
    """
    Encrypt *plaintext* and return (ciphertext_b64, salt_b64).
    Both strings are safe to store in JSON.
    """
    salt = os.urandom(16)
    key = _derive_key(salt)
    token = Fernet(key).encrypt(plaintext.encode("utf-8"))
    return (
        base64.urlsafe_b64encode(token).decode("ascii"),
        base64.urlsafe_b64encode(salt).decode("ascii"),
    )


def decrypt(ciphertext_b64: str, salt_b64: str) -> str:
    """
    Decrypt a value previously produced by `encrypt`.
    Returns the original plaintext, or raises ValueError on failure.
    """
    try:
        salt = base64.urlsafe_b64decode(salt_b64.encode("ascii"))
        token = base64.urlsafe_b64decode(ciphertext_b64.encode("ascii"))
        key = _derive_key(salt)
        return Fernet(key).decrypt(token).decode("utf-8")
    except (InvalidToken, Exception) as e:
        raise ValueError("פענוח הסיסמה נכשל — ייתכן שהנתונים פגומים") from e
