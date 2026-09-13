"""Lectura de teclado no bloqueante y multiplataforma.

Se usa en el modo auto-batalla (`combat/battle.py`) para poder cancelar pulsando
`q` sin bloquear el bucle de combate:

- **Windows**: `msvcrt.kbhit()` / `msvcrt.getch()`.
- **POSIX**: `select` sobre `stdin` con la terminal en modo *cbreak* temporal.
- **Sin terminal interactivo** (tests, salida redirigida, un `.exe` lanzado sin
  consola): `key_pressed()` devuelve siempre `None`.

Antes esto vivía como `import msvcrt` a nivel de módulo en `battle.py`, lo que
ataba todo el proyecto (y su suite de tests) a Windows. Las ramas que hablan de
verdad con la terminal llevan `# pragma: no cover`: no hay una terminal
interactiva ni en CI ni bajo pytest.
"""

from __future__ import annotations

import sys

if sys.platform == "win32":  # pragma: no cover - depende del SO
    import msvcrt

    def _win_key_pressed() -> str | None:
        if msvcrt.kbhit():
            return msvcrt.getch().decode(errors="ignore").lower() or None
        return None

else:
    import select
    import termios
    import tty

    def _posix_key_pressed() -> str | None:  # pragma: no cover - necesita terminal real
        fd = sys.stdin.fileno()
        try:
            old = termios.tcgetattr(fd)
        except termios.error:
            return None
        try:
            tty.setcbreak(fd)
            if select.select([sys.stdin], [], [], 0)[0]:
                return sys.stdin.read(1).lower() or None
            return None
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)


def key_pressed() -> str | None:
    """La tecla que hay esperando en la entrada (un carácter en minúscula), o
    `None` si no hay ninguna. Nunca bloquea."""
    if sys.platform == "win32":  # pragma: no cover - se prueba en el job de Windows
        return _win_key_pressed()
    if not sys.stdin.isatty():
        return None
    return _posix_key_pressed()
