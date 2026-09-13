"""Rutas centralizadas del proyecto, resueltas de forma absoluta."""

import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    # Empaquetado con PyInstaller: los assets (solo lectura) viven dentro del
    # bundle (sys._MEIPASS, un directorio temporal en --onefile o la propia
    # carpeta de salida en --onedir); lo que el juego escribe (config.ini,
    # partidas guardadas) debe vivir junto al .exe, no dentro del bundle, o se
    # perdería entre ejecuciones (y en --onefile, dentro del propio proceso).
    BASE_DIR: Path = Path(sys.executable).resolve().parent
    ASSETS_DIR: Path = Path(getattr(sys, "_MEIPASS", BASE_DIR)) / "assets"
else:
    # src/valeterna/config/paths.py -> raíz del repo (4 niveles arriba)
    BASE_DIR = Path(__file__).resolve().parents[3]
    ASSETS_DIR = BASE_DIR / "assets"

SAVE_DIR: Path = BASE_DIR / "saved_games"
CONFIG_FILE: Path = BASE_DIR / "config.ini"
