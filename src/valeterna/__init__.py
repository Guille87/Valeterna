"""Juego de Rol por Turnos — RPG de batalla por turnos en consola."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("valeterna")
except PackageNotFoundError:  # ejecutado sin instalar (p. ej. tests sobre el source)
    __version__ = "0.0.0.dev0"

__all__ = ["__version__"]
