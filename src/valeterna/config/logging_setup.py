"""Registro de errores en disco.

Cuando el juego se reparte como .exe y peta en el ordenador de otra persona, la
ventana se cierra y no queda ni rastro de qué pasó. Este módulo:

- Escribe un log rotativo en ``BASE_DIR/logs/juego.log`` (junto al .exe cuando
  está empaquetado), con la traza completa de cualquier error.
- Captura también las excepciones que se escapan del ``try`` de ``app.main()``
  y las que revientan en hilos en segundo plano (el watchdog de música).
- Deja un ``crash_...txt`` aparte y bien visible por cada cierre inesperado,
  para que quien lo sufra solo tenga que mandarte ese archivo.

No envía nada por red: todo se queda en el equipo del jugador.
"""

from __future__ import annotations

import datetime as _dt
import logging
import logging.handlers
import platform
import sys
import threading
import traceback
from pathlib import Path

from valeterna.config.paths import BASE_DIR

LOG_DIR: Path = BASE_DIR / "logs"
LOG_FILE: Path = LOG_DIR / "juego.log"

logger = logging.getLogger("valeterna")

_configured = False


def _game_version() -> str:
    from valeterna import __version__

    return __version__


def setup_logging() -> None:
    """Configura el logging a fichero. Idempotente."""
    global _configured
    if _configured:
        return

    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
    except OSError:
        # Si ni siquiera podemos crear la carpeta de logs, seguimos sin logging
        # a fichero antes que impedir que el juego arranque.
        _configured = True
        return

    handler = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    logger.propagate = False

    # Excepciones que no captura nadie más (hilo principal).
    sys.excepthook = _handle_uncaught

    # Excepciones en hilos (Python 3.8+): el watchdog de música, sobre todo.
    if hasattr(threading, "excepthook"):
        threading.excepthook = _handle_thread_exception

    _configured = True
    logger.info(
        "=== Sesión iniciada | versión %s | Python %s | %s ===",
        _game_version(),
        platform.python_version(),
        platform.platform(),
    )


def log_session_end() -> None:
    if _configured:
        logger.info("=== Sesión finalizada con normalidad ===")


def report_crash(exc: BaseException, *, context: str = "bucle principal") -> Path | None:
    """Registra un cierre inesperado y escribe un crash_...txt aparte.

    Devuelve la ruta del crash_...txt (o None si no se pudo escribir), para
    poder decírsela al jugador por pantalla.
    """
    if _configured:
        logger.critical("CRASH en %s", context, exc_info=exc)

    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    crash_path = LOG_DIR / f"crash_{stamp}.txt"
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        crash_path.write_text(
            f"Juego de Rol por Turnos - informe de cierre inesperado\n"
            f"Fecha: {_dt.datetime.now().isoformat(timespec='seconds')}\n"
            f"Versión: {_game_version()}\n"
            f"Python: {platform.python_version()}\n"
            f"Sistema: {platform.platform()}\n"
            f"Contexto: {context}\n"
            f"Empaquetado (.exe): {bool(getattr(sys, 'frozen', False))}\n"
            f"\n{'-' * 60}\n{tb}",
            encoding="utf-8",
        )
        return crash_path
    except OSError:
        return None


def _handle_uncaught(exc_type, exc_value, exc_tb) -> None:
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_tb)
        return
    report_crash(exc_value, context="excepción no capturada")
    sys.__excepthook__(exc_type, exc_value, exc_tb)


def _handle_thread_exception(args) -> None:
    if issubclass(args.exc_type, SystemExit):
        return
    if _configured:
        logger.error(
            "Excepción en hilo %s",
            getattr(args.thread, "name", "?"),
            exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
        )
