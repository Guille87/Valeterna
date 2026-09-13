import contextlib
import logging
import sys
import threading

import pygame
from colorama import init

from valeterna import i18n, updater
from valeterna.audio.catalog import AUDIO_ASSETS
from valeterna.audio.resource_manager import ResourceManager
from valeterna.config import crash_reporting, paths, settings
from valeterna.config.logging_setup import (
    LOG_FILE,
    log_session_end,
    report_crash,
    setup_logging,
)
from valeterna.ui import console
from valeterna.ui.menus import ask_crash_reporting_opt_in, main_menu


def setup_resources() -> None:
    """Inicializa el ResourceManager y carga los archivos de audio."""
    rm = ResourceManager()

    # 1. Cargar volúmenes desde config.ini antes de cargar audios
    music_vol, sfx_vol = settings.load_config()
    rm.set_volume_music(music_vol)
    rm.set_volume_sfx(sfx_vol)

    # 2. Cargar Música
    for name, relative_path in AUDIO_ASSETS["music"].items():
        full_path = paths.ASSETS_DIR / relative_path
        rm.load_audio(name, str(full_path), is_music=True)

    # 3. Cargar Efectos
    for name, relative_path in AUDIO_ASSETS["sfx"].items():
        full_path = paths.ASSETS_DIR / relative_path
        rm.load_audio(name, str(full_path), is_music=False)


_music_watchdog_stop = threading.Event()


def _music_watchdog() -> None:
    """Hilo en segundo plano que revisa cada pocos segundos si la música ha
    terminado y hay que poner la siguiente. Hace falta porque el juego es una
    consola síncrona: la mayor parte del tiempo está bloqueada en input()
    esperando al jugador, así que sin este hilo la música se quedaría en
    silencio en cuanto una pista terminara y el jugador no hiciera nada."""
    rm = ResourceManager()
    while not _music_watchdog_stop.wait(2):
        try:
            rm.update()
        except Exception:
            # No queremos tumbar el juego por un fallo de audio en segundo plano,
            # pero sí dejar constancia en el log para poder investigarlo luego.
            logging.getLogger("valeterna.audio").warning("Fallo en el watchdog de música", exc_info=True)


def main() -> None:
    # Forzamos stdout/stderr a UTF-8 antes de nada: en una consola de Windows
    # con code page heredada (cmd.exe por defecto, o el .exe empaquetado fuera
    # de un IDE) los emojis/tildes de los textos del juego revientan con
    # UnicodeEncodeError si no se hace esto. Debe ir antes de colorama.init(),
    # que envuelve stdout/stderr con su propio wrapper.
    for stream in (sys.stdout, sys.stderr):
        with contextlib.suppress(AttributeError, ValueError):
            # .reconfigure() solo existe en TextIOWrapper, no en el TextIO genérico
            # de los stubs; el AttributeError capturado cubre el caso contrario.
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]

    # Registro de errores en disco: a partir de aquí cualquier fallo queda
    # escrito en logs/juego.log (junto al .exe si está empaquetado).
    setup_logging()

    # Idioma de los textos del juego (config.ini [IDIOMA]).
    i18n.set_locale(settings.load_language())

    # Inicialización de librerías
    init(autoreset=True)  # Colorama
    pygame.init()
    pygame.mixer.init()

    watchdog = None
    crashed = False
    _music_watchdog_stop.clear()
    try:
        setup_resources()

        # Si hay un webhook configurado y el jugador aún no ha decidido, le
        # preguntamos una sola vez si quiere enviar informes de error.
        if crash_reporting.is_configured():
            ask_crash_reporting_opt_in()

        # En la build empaquetada, comprobamos en segundo plano si hay una
        # versión más nueva publicada (el resultado se muestra en el menú).
        if updater.is_active() and settings.load_update_check():
            updater.start_background_check()

        # Iniciar música inicial
        rm = ResourceManager()
        rm.update()

        # Hilo en segundo plano para que la música siga avanzando aunque el
        # juego esté bloqueado esperando input() del jugador.
        watchdog = threading.Thread(target=_music_watchdog, daemon=True)
        watchdog.start()

        # Lanzar el bucle principal del juego (Menú)
        main_menu()

    except Exception as e:
        crashed = True
        crash_path = report_crash(e, context="app.main")
        console.error(f"\nError crítico durante la ejecución: {e}")
        console.warning("\nEl juego se ha cerrado por un error inesperado. Se ha guardado un informe en:")
        print(f"  {crash_path or LOG_FILE}")

        if settings.load_crash_reporting() is True and crash_reporting.is_configured():
            if crash_reporting.send_crash_report(crash_path, e, context="app.main"):
                console.info("Se ha enviado un informe automático al desarrollador. ¡Gracias!")
            else:
                console.warning("Envíame ese archivo y podré ver exactamente qué ha fallado.")
        else:
            console.warning("Envíame ese archivo y podré ver exactamente qué ha fallado.")
    else:
        log_session_end()
    finally:
        # Paramos el hilo de música y esperamos a que acabe su vuelta actual
        # ANTES de cerrar el mezclador, si no puede intentar reproducir música
        # con el dispositivo de audio ya cerrado ("Audio device hasn't been opened").
        _music_watchdog_stop.set()
        updater.stop_background_check()
        if watchdog is not None:
            watchdog.join(timeout=3)
        pygame.mixer.quit()
        pygame.quit()

        # La ventana de un .exe se cierra sola al terminar el proceso: si ha
        # habido un crash, esperamos a que el jugador pueda leer la ruta del
        # informe antes de que desaparezca todo.
        if crashed:
            with contextlib.suppress(EOFError, KeyboardInterrupt):
                input("\nPulsa Enter para cerrar...")


if __name__ == "__main__":
    main()
