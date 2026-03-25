import pytest
from services.crypto_service import decrypt, encrypt


def test_encrypt_returns_two_strings():
    ciphertext, salt = encrypt("hello")
    assert isinstance(ciphertext, str) and len(ciphertext) > 0
    assert isinstance(salt, str) and len(salt) > 0


def test_decrypt_recovers_plaintext():
    ciphertext, salt = encrypt("my secret password")
    assert decrypt(ciphertext, salt) == "my secret password"


def test_encrypt_produces_different_ciphertexts_each_time():
    ct1, _ = encrypt("same")
    ct2, _ = encrypt("same")
    assert ct1 != ct2  # random salt → different ciphertext


def test_decrypt_with_wrong_salt_raises():
    ciphertext, _ = encrypt("secret")
    _, other_salt = encrypt("other")
    with pytest.raises(ValueError):
        decrypt(ciphertext, other_salt)


def test_decrypt_with_tampered_ciphertext_raises():
    ciphertext, salt = encrypt("secret")
    tampered = ciphertext[:-4] + "XXXX"
    with pytest.raises(ValueError):
        decrypt(tampered, salt)


def test_roundtrip_hebrew_text():
    plaintext = "סיסמה בעברית 123!"
    ct, salt = encrypt(plaintext)
    assert decrypt(ct, salt) == plaintext


def test_roundtrip_empty_string():
    ct, salt = encrypt("")
    assert decrypt(ct, salt) == ""


def test_settings_service_set_and_get_secret(tmp_path, monkeypatch):
    """set_secret stores encrypted data; get_secret decrypts it correctly."""
    import services.settings_service as ss_module

    settings_path = str(tmp_path / "settings.json")
    monkeypatch.setattr(ss_module, "_SETTINGS_PATH", settings_path)

    from services.settings_service import SettingsService
    svc = SettingsService()

    svc.set_secret("backup_password", "hunter2")
    assert svc.get_secret("backup_password") == "hunter2"

    # Verify the raw JSON does NOT contain the plaintext
    import json
    with open(settings_path) as f:
        raw = json.load(f)
    assert raw["backup_password"] != "hunter2"
    assert "enc" in raw["backup_password"]
    assert "salt" in raw["backup_password"]


def test_settings_service_get_secret_default_when_missing(tmp_path, monkeypatch):
    import services.settings_service as ss_module

    settings_path = str(tmp_path / "settings.json")
    monkeypatch.setattr(ss_module, "_SETTINGS_PATH", settings_path)

    from services.settings_service import SettingsService
    svc = SettingsService()

    assert svc.get_secret("missing_key") == ""
    assert svc.get_secret("missing_key", "fallback") == "fallback"


def test_settings_service_get_secret_backwards_compat(tmp_path, monkeypatch):
    """Plain-text values written by older versions are returned as-is."""
    import json
    import services.settings_service as ss_module

    settings_path = str(tmp_path / "settings.json")
    with open(settings_path, "w") as f:
        json.dump({"backup_password": "old_plain_text"}, f)

    monkeypatch.setattr(ss_module, "_SETTINGS_PATH", settings_path)

    from services.settings_service import SettingsService
    svc = SettingsService()

    assert svc.get_secret("backup_password") == "old_plain_text"
