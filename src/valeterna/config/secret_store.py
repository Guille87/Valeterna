"""Acceso tolerante a ``config/secrets.py``.

``secrets.py`` contiene datos sensibles y NO se versiona (está en ``.gitignore``).
En un clon recién hecho no existe: en ese caso este módulo devuelve los valores
por defecto y el juego sigue funcionando (sin envío de crashes a Discord, sin
modo admin), en vez de reventar al importar.

Para activarlo: copia ``config/secrets.example.py`` a ``config/secrets.py`` y
rellena los valores.
"""

from __future__ import annotations

try:  # pragma: no cover - depende de si existe secrets.py en la máquina
    from valeterna.config import secrets as _secrets  # type: ignore[attr-defined]
except Exception:  # ImportError o cualquier fallo al cargarlo
    _secrets = None


def get(name: str, default: str = "") -> str:
    """Devuelve el secreto ``name`` de secrets.py, o ``default`` si no está."""
    if _secrets is None:
        return default
    value = getattr(_secrets, name, None)
    return value if value else default
