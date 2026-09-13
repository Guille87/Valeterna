import getpass
import io

import pytest

from valeterna.config import crash_reporting


@pytest.fixture(autouse=True)
def _no_real_secrets(monkeypatch):
    """Neutraliza config/secrets.py para que los tests no dependan de si en esta
    máquina hay un webhook/ID reales configurados."""
    monkeypatch.delenv("JRT_CRASH_WEBHOOK", raising=False)
    monkeypatch.setattr(crash_reporting, "WEBHOOK_URL", "")
    monkeypatch.setattr(crash_reporting.secret_store, "get", lambda name, default="": default)


def test_scrub_removes_username_and_home(monkeypatch):
    monkeypatch.setattr(getpass, "getuser", lambda: "pepito")
    text = r"C:\Users\pepito\juego\logs\crash.txt y /home/pepito/x - hola pepito"
    out = crash_reporting.scrub(text)
    assert "pepito" not in out
    assert "<usuario>" in out


def test_scrub_generic_windows_path_even_without_matching_user(monkeypatch):
    monkeypatch.setattr(getpass, "getuser", lambda: "otro")
    out = crash_reporting.scrub(r'File "C:\Users\alguien\app.py"')
    assert r"C:\Users\<usuario>" in out


def test_send_returns_false_when_no_webhook():
    assert crash_reporting.is_configured() is False
    assert crash_reporting.send_crash_report(None, ValueError("x"), context="t") is False


def test_send_never_raises_on_network_error(monkeypatch):
    monkeypatch.setattr(crash_reporting, "WEBHOOK_URL", "http://example.invalid/webhook")

    def boom(*a, **k):
        raise OSError("sin red")

    monkeypatch.setattr(crash_reporting.urllib.request, "urlopen", boom)
    assert crash_reporting.send_crash_report(None, ValueError("x"), context="t") is False


def test_send_posts_multipart_with_scrubbed_file(monkeypatch, tmp_path):
    monkeypatch.setattr(getpass, "getuser", lambda: "pepito")
    monkeypatch.setattr(crash_reporting, "WEBHOOK_URL", "http://example.invalid/webhook")

    crash_file = tmp_path / "crash_x.txt"
    crash_file.write_text("Traceback...\nC:\\Users\\pepito\\app.py\n", encoding="utf-8")

    sent = {}

    def fake_urlopen(req, timeout=None):
        sent["ctype"] = req.headers.get("Content-type")
        sent["ua"] = req.headers.get("User-agent")
        sent["body"] = req.data
        return io.BytesIO(b"")

    monkeypatch.setattr(crash_reporting.urllib.request, "urlopen", fake_urlopen)

    ok = crash_reporting.send_crash_report(crash_file, ValueError("bum"), context="app.main")

    assert ok is True
    assert "multipart/form-data" in sent["ctype"]
    # Discord rechaza (403) el User-Agent por defecto de urllib: debe ir uno propio.
    assert sent["ua"] and "Python-urllib" not in sent["ua"]
    body = sent["body"].decode("utf-8", "replace")
    assert 'filename="crash_x.txt"' in body
    assert "pepito" not in body  # el fichero va scrubeado
    assert "<usuario>" in body


def _capture_urlopen(sent):
    def fake_urlopen(req, timeout=None):
        sent["body"] = req.data
        return io.BytesIO(b"")

    return fake_urlopen


def test_mention_prefix_added_when_user_id_configured(monkeypatch):
    monkeypatch.setattr(crash_reporting, "WEBHOOK_URL", "http://example.invalid/webhook")
    monkeypatch.setattr(
        crash_reporting.secret_store,
        "get",
        lambda name, default="": "123456789012345678" if name == "CRASH_MENTION_USER_ID" else default,
    )
    sent = {}
    monkeypatch.setattr(crash_reporting.urllib.request, "urlopen", _capture_urlopen(sent))

    crash_reporting.send_crash_report(None, ValueError("bum"), context="t")

    body = sent["body"].decode("utf-8", "replace")
    assert "<@123456789012345678>" in body
    assert '"users": ["123456789012345678"]' in body


def test_no_mention_when_user_id_missing(monkeypatch):
    monkeypatch.setattr(crash_reporting, "WEBHOOK_URL", "http://example.invalid/webhook")
    sent = {}
    monkeypatch.setattr(crash_reporting.urllib.request, "urlopen", _capture_urlopen(sent))

    crash_reporting.send_crash_report(None, ValueError("bum"), context="t")

    assert "<@" not in sent["body"].decode("utf-8", "replace")
