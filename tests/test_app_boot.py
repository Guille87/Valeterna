"""Smoke test de arranque: `app.main()` monta todo (logging, pygame, audio, el
watchdog de música, el menú principal) y sale limpiamente al elegir "Salir".

`app.py` y `ui/menus.py` están fuera de la medición de cobertura, pero este test
sí garantiza que el juego *arranca* — pilla errores de wiring/imports que los
tests unitarios no ven.
"""

import sys
import threading

import pygame
import pytest

from valeterna import app
from valeterna.config import logging_setup


@pytest.fixture(autouse=True)
def _restore_after_main(monkeypatch):
    # main() cierra el mixer y toca los excepthook en su finally: lo dejamos
    # todo como estaba para no romper el resto de la sesión de tests.
    monkeypatch.setattr(sys, "excepthook", sys.excepthook)
    monkeypatch.setattr(threading, "excepthook", threading.excepthook)
    yield
    if not pygame.mixer.get_init():
        pygame.mixer.init()


def test_app_main_boots_and_exits_cleanly(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(logging_setup, "LOG_DIR", tmp_path)
    monkeypatch.setattr(logging_setup, "LOG_FILE", tmp_path / "juego.log")
    monkeypatch.setattr(logging_setup, "_configured", False)
    # No preguntar por el opt-in de informes de error (tocaría el config.ini real).
    monkeypatch.setattr(app, "ask_crash_reporting_opt_in", lambda: None)
    # En el menú principal elegimos "4" = Salir en la primera vuelta.
    monkeypatch.setattr("valeterna.ui.menus.console.ask", lambda prompt: "4")

    app.main()  # no debe lanzar

    out = capsys.readouterr().out
    assert "MENÚ PRINCIPAL" in out
    assert (tmp_path / "juego.log").exists()
    assert "Sesión finalizada con normalidad" in (tmp_path / "juego.log").read_text(encoding="utf-8")
    assert app._music_watchdog_stop.is_set()  # el watchdog se paró en el finally
