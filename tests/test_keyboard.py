import sys

import pytest

from valeterna.combat import battle
from valeterna.ui import keyboard


def test_key_pressed_returns_none_without_a_waiting_key():
    """En pytest stdin no es un terminal interactivo (rama POSIX) y en Windows
    msvcrt.kbhit() es False sin pulsaciones: en ambos casos, None."""
    assert keyboard.key_pressed() is None


@pytest.mark.skipif(sys.platform != "win32", reason="rama de msvcrt")
def test_key_pressed_windows_reads_and_lowercases_the_key(monkeypatch):
    monkeypatch.setattr(keyboard.msvcrt, "kbhit", lambda: True)
    monkeypatch.setattr(keyboard.msvcrt, "getch", lambda: b"Q")
    assert keyboard.key_pressed() == "q"

    monkeypatch.setattr(keyboard.msvcrt, "kbhit", lambda: False)
    assert keyboard.key_pressed() is None


def test_check_for_interrupt_only_fires_on_q(monkeypatch):
    monkeypatch.setattr(battle, "key_pressed", lambda: "q")
    assert battle.check_for_interrupt() is True

    monkeypatch.setattr(battle, "key_pressed", lambda: "x")
    assert battle.check_for_interrupt() is False

    monkeypatch.setattr(battle, "key_pressed", lambda: None)
    assert battle.check_for_interrupt() is False
