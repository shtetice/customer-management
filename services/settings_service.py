import json
import os


_SETTINGS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "settings.json")
_SETTINGS_PATH = os.path.normpath(_SETTINGS_PATH)


class SettingsService:

    def __init__(self):
        self._path = _SETTINGS_PATH
        self._data: dict = {}
        self._load()

    def _load(self):
        if os.path.exists(self._path):
            try:
                with open(self._path, encoding="utf-8") as f:
                    self._data = json.load(f)
            except Exception:
                self._data = {}

    def _save(self):
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value):
        self._data[key] = value
        self._save()

    # ── Encrypted secret helpers ──────────────────────────────

    def set_secret(self, key: str, plaintext: str):
        """Encrypt *plaintext* and store it under *key* in settings.json."""
        from services.crypto_service import encrypt
        ciphertext, salt = encrypt(plaintext)
        self._data[key] = {"enc": ciphertext, "salt": salt}
        self._save()

    def get_secret(self, key: str, default: str = "") -> str:
        """Decrypt and return the secret stored under *key*, or *default* if absent."""
        from services.crypto_service import decrypt
        entry = self._data.get(key)
        if not entry or not isinstance(entry, dict):
            # Fall back gracefully for plain-text values written by older versions
            return entry if isinstance(entry, str) else default
        try:
            return decrypt(entry["enc"], entry["salt"])
        except Exception:
            return default


settings_service = SettingsService()
