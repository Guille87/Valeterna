from valeterna.config import secret_store


class _FakeSecrets:
    CRASH_WEBHOOK_URL = "https://example.invalid/webhook"
    ADMIN_PASSWORD_HASH = ""


def test_get_returns_default_when_secrets_module_missing(monkeypatch):
    monkeypatch.setattr(secret_store, "_secrets", None)
    assert secret_store.get("CRASH_WEBHOOK_URL", "por-defecto") == "por-defecto"
    assert secret_store.get("CUALQUIERA") == ""


def test_get_returns_value_when_present(monkeypatch):
    monkeypatch.setattr(secret_store, "_secrets", _FakeSecrets)
    assert secret_store.get("CRASH_WEBHOOK_URL") == "https://example.invalid/webhook"


def test_get_returns_default_when_attribute_missing(monkeypatch):
    monkeypatch.setattr(secret_store, "_secrets", _FakeSecrets)
    assert secret_store.get("NO_EXISTE", "fallback") == "fallback"


def test_get_returns_default_when_value_is_empty(monkeypatch):
    """Un secreto presente pero vacío cuenta como "no configurado"."""
    monkeypatch.setattr(secret_store, "_secrets", _FakeSecrets)
    assert secret_store.get("ADMIN_PASSWORD_HASH", "fallback") == "fallback"
