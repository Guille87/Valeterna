"""Modo DEBUG (v0.14.x): activado solo por la variable de entorno
VALETERNA_DEBUG (config/debug.py). Ver tests/test_formatting.py para dónde
se usa (el poder de jugador/enemigo en print_player_enemy_info)."""

from valeterna.config.debug import is_debug


def test_debug_is_off_by_default(monkeypatch):
    monkeypatch.delenv("VALETERNA_DEBUG", raising=False)
    assert is_debug() is False


def test_debug_recognises_truthy_values(monkeypatch):
    for value in ("1", "true", "True", "YES", "on"):
        monkeypatch.setenv("VALETERNA_DEBUG", value)
        assert is_debug() is True, value


def test_debug_rejects_other_values(monkeypatch):
    for value in ("0", "false", "no", "off", ""):
        monkeypatch.setenv("VALETERNA_DEBUG", value)
        assert is_debug() is False, value
