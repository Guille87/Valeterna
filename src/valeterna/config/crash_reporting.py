"""Envío opcional de informes de error a un webhook de Discord.

Mismo patrón que el bot Vektra: un POST a la URL del webhook. Aquí, además del
mensaje, se adjunta el ``crash_*.txt`` completo (ya "scrubeado": sin el nombre
de usuario de Windows ni rutas personales).

- Solo se envía si el jugador lo ha aceptado (``settings.load_crash_reporting()``).
- Nunca lanza: si Discord no responde, o no hay internet, o la URL está vacía,
  se traga el error (queda en el log local igualmente).
- Sin dependencias externas: usa ``urllib`` de la stdlib.

La URL del webhook se toma, por orden, de:
  1. la variable de entorno ``JRT_CRASH_WEBHOOK`` (útil en desarrollo/CI),
  2. la constante ``WEBHOOK_URL`` de abajo (vacía en el repo),
  3. ``CRASH_WEBHOOK_URL`` en ``config/secrets.py`` (no versionado — ver
     ``config/secrets.example.py``).

Una URL de webhook de Discord es semi-secreta: cualquiera que la tenga puede
publicar en el canal. Si alguien la extrae del .exe y hace spam, basta con
borrar el webhook en Discord y crear otro.
"""

from __future__ import annotations

import getpass
import json
import logging
import os
import platform
import re
import urllib.request
import uuid
from pathlib import Path

from valeterna.config import secret_store

logger = logging.getLogger("valeterna.reportes")

# Override opcional por código; normalmente vacío (la URL vive en secrets.py).
WEBHOOK_URL: str = ""

_TIMEOUT_S = 6

# Discord rechaza con 403 las peticiones que llevan el User-Agent por defecto de
# urllib (o ninguno): hay que mandar uno propio.
_USER_AGENT = "Valeterna (https://github.com/Guille87, crash-reporter)"


def _webhook_url() -> str:
    return (
        os.environ.get("JRT_CRASH_WEBHOOK", "").strip()
        or WEBHOOK_URL.strip()
        or secret_store.get("CRASH_WEBHOOK_URL").strip()
    )


def _mention_prefix() -> str:
    """`<@ID> ` para que Discord notifique al desarrollador, o '' si no hay ID."""
    uid = secret_store.get("CRASH_MENTION_USER_ID").strip()
    return f"<@{uid}> " if uid.isdigit() else ""


def scrub(text: str) -> str:
    """Quita datos personales del texto antes de enviarlo fuera del equipo:
    el nombre de usuario del sistema y las rutas del perfil del usuario."""
    if not text:
        return text

    replacements = []

    try:
        user = getpass.getuser()
        if user:
            replacements.append((user, "<usuario>"))
    except Exception:
        pass

    try:
        home = os.path.expanduser("~")
        if home and home != "~":
            replacements.append((home, "<HOME>"))
    except Exception:
        pass

    for needle, repl in replacements:
        text = text.replace(needle, repl)
        # Rutas de Windows con separador invertido escapado en tracebacks.
        text = text.replace(needle.replace("\\", "\\\\"), repl)

    # Red de seguridad genérica: C:\Users\X\  /home/X/  /Users/X/
    text = re.sub(r"([Cc]:\\Users\\)[^\\\/]+", r"\1<usuario>", text)
    text = re.sub(r"(/(?:home|Users)/)[^/]+", r"\1<usuario>", text)
    return text


def _game_version() -> str:
    from valeterna import __version__

    return __version__


def is_configured() -> bool:
    return bool(_webhook_url())


def send_crash_report(crash_path: Path | None, exc: BaseException, *, context: str) -> bool:
    """Envía el informe al webhook de Discord. Devuelve True si Discord acepta."""
    url = _webhook_url()
    if not url:
        return False

    header = (
        f"{_mention_prefix()}**Cierre inesperado** · v{_game_version()} · "
        f"{platform.system()} {platform.release()} · contexto: `{context}`\n"
        f"`{type(exc).__name__}: {exc}`"
    )
    header = scrub(header)[:1900]

    body_bytes = b""
    filename = "crash.txt"
    if crash_path and crash_path.exists():
        try:
            body_bytes = scrub(crash_path.read_text(encoding="utf-8")).encode("utf-8")
            filename = crash_path.name
        except OSError:
            body_bytes = b""

    try:
        if body_bytes:
            _post_multipart(url, header, filename, body_bytes)
        else:
            _post_json(url, _payload(header))
        return True
    except Exception as e:  # noqa: BLE001 - nunca debe tumbar el cierre del juego
        logger.warning("No se pudo enviar el informe de error a Discord: %s", e)
        return False


def _payload(content: str) -> dict:
    """Cuerpo JSON para Discord. Restringe las menciones al ID del desarrollador
    (si lo hay) para que nunca se cuele un @everyone desde el texto de un error."""
    uid = secret_store.get("CRASH_MENTION_USER_ID").strip()
    allowed = {"parse": [], "users": [uid]} if uid.isdigit() else {"parse": []}
    return {"content": content, "allowed_mentions": allowed}


def _post_json(url: str, payload: dict) -> None:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": _USER_AGENT},
        method="POST",
    )
    urllib.request.urlopen(req, timeout=_TIMEOUT_S).close()


def _post_multipart(url: str, content: str, filename: str, file_bytes: bytes) -> None:
    boundary = uuid.uuid4().hex
    payload_json = json.dumps(_payload(content)).encode("utf-8")

    parts = [
        b"--" + boundary.encode() + b"\r\n",
        b'Content-Disposition: form-data; name="payload_json"\r\n',
        b"Content-Type: application/json\r\n\r\n",
        payload_json,
        b"\r\n--" + boundary.encode() + b"\r\n",
        f'Content-Disposition: form-data; name="files[0]"; filename="{filename}"\r\n'.encode(),
        b"Content-Type: text/plain; charset=utf-8\r\n\r\n",
        file_bytes,
        b"\r\n--" + boundary.encode() + b"--\r\n",
    ]
    body = b"".join(parts)
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "User-Agent": _USER_AGENT,
        },
        method="POST",
    )
    urllib.request.urlopen(req, timeout=_TIMEOUT_S).close()
