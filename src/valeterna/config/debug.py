"""Modo DEBUG (v0.14.x, petición del usuario): activado solo por la variable
de entorno `VALETERNA_DEBUG`, nunca desde dentro del juego (ni siquiera con
el personaje "admin" — es un modo de desarrollo/testeo, no un cheat para
jugar). Mismo patrón que otras banderas por entorno del proyecto (`$CI` en
`updater.py`, `$JRT_CRASH_WEBHOOK` en `crash_reporting.py`)."""

import os


def is_debug() -> bool:
    return os.environ.get("VALETERNA_DEBUG", "").strip().lower() in {"1", "true", "yes", "on"}
