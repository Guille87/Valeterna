"""Auto-actualización de la build de Windows.

El juego se reparte como un paquete PyInstaller `--onedir`. Este módulo detecta
si hay una versión más nueva publicada en el GitHub Release, avisa en el menú y
—si el jugador lo pide— la descarga, la verifica por SHA-256 y la aplica
reiniciándose, sin tocar `saved_games/` / `config.ini`.

Aplicar la actualización con el `.exe` en marcha es imposible en Windows (los
archivos están bloqueados), así que `apply_and_restart()` escribe un `.bat` que
espera a que el juego se cierre, copia la versión nueva encima y relanza.

Solo hace algo en la build empaquetada (`sys.frozen`). Ejecutando desde el código
fuente (`python main.py`) todo es no-op: ahí se actualiza con `git`.

Seguridad (v1): HTTPS a la API de GitHub + verificación del SHA-256 publicado en
el mismo Release + protección anti-downgrade. No protege ante una cuenta de
GitHub comprometida; eso lo daría una firma (ver SECURITY.md), que se puede
añadir después en `verify()`.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
import zipfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn

logger = logging.getLogger("valeterna.updater")

GITHUB_REPO = "Guille87/Valeterna"
_API_LATEST = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
_USER_AGENT = "Valeterna-updater (https://github.com/Guille87/Valeterna)"
_TIMEOUT_S = 10


@dataclass(frozen=True)
class UpdateInfo:
    version: str  # "0.4.0"
    tag: str  # "v0.4.0"
    zip_url: str  # browser_download_url del asset "...-windows.zip"
    sha256: str | None  # de SHA256SUMS, o None si el Release no lo trae
    notes: str  # cuerpo del Release, recortado


def is_active() -> bool:
    """Solo en la build empaquetada, y nunca dentro de CI."""
    return bool(getattr(sys, "frozen", False)) and not os.environ.get("CI")


def _version_tuple(text: str) -> tuple[int, ...]:
    """`"v1.2.3"` / `"1.2.3-rc1"` -> `(1, 2, 3)`. Toma los dígitos iniciales de
    cada parte (los tags del proyecto son siempre `vX.Y.Z`, sin pre-releases)."""
    parts = []
    for chunk in text.strip().lstrip("vV").split("."):
        leading = ""
        for c in chunk:
            if not c.isdigit():
                break
            leading += c
        parts.append(int(leading) if leading else 0)
    return tuple(parts) or (0,)


def _current_version() -> str:
    from valeterna import __version__

    return __version__


def _get_json(url: str) -> dict | list:  # pragma: no cover - I/O de red, se mockea en tests
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT, "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get_text(url: str) -> str:  # pragma: no cover - I/O de red, se mockea en tests
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _sha_for(zip_name: str, sha_sums_url: str | None) -> str | None:
    """Descarga SHA256SUMS y devuelve el hash de la línea del zip, o None."""
    if not sha_sums_url:
        return None
    try:
        for line in _get_text(sha_sums_url).splitlines():
            parts = line.split()
            if len(parts) == 2 and parts[1].lstrip("*") == zip_name:
                return parts[0].lower()
    except Exception as exc:  # noqa: BLE001 - el updater nunca debe lanzar
        logger.warning("No se pudo leer SHA256SUMS: %s", exc)
    return None


def _do_check() -> UpdateInfo | None:
    try:
        data = _get_json(_API_LATEST)
        assert isinstance(data, dict)
        tag = data["tag_name"]
        if _version_tuple(tag) <= _version_tuple(_current_version()):
            return None

        assets = {a["name"]: a["browser_download_url"] for a in data.get("assets", [])}
        zip_name = next((n for n in assets if n.endswith("-windows.zip")), None)
        if not zip_name:
            logger.warning("El Release %s no tiene un asset -windows.zip", tag)
            return None

        return UpdateInfo(
            version=tag.lstrip("vV"),
            tag=tag,
            zip_url=assets[zip_name],
            sha256=_sha_for(zip_name, assets.get("SHA256SUMS")),
            notes=(data.get("body") or "").strip()[:1500],
        )
    except Exception as exc:  # noqa: BLE001 - el updater nunca debe tumbar el juego
        logger.warning("Fallo comprobando actualizaciones: %s", exc)
        return None


# --- Comprobación en segundo plano (mismo patrón que el watchdog de música) ---

_available: UpdateInfo | None = None
_stop = threading.Event()
_thread: threading.Thread | None = None


def check() -> UpdateInfo | None:
    """Consulta el último Release y guarda el resultado en `available()`. Devuelve
    `UpdateInfo` solo si su versión es estrictamente mayor que la instalada y trae
    un `.zip` de Windows; `None` en cualquier otro caso (igual/menor versión, sin
    asset, error de red...). Un fallo de red no borra un aviso ya encontrado."""
    global _available
    info = _do_check()
    if info is not None:
        _available = info
        logger.info("Actualización disponible: %s", info.tag)
    return info


def _worker() -> None:
    cleanup_staging()
    if not _stop.is_set():
        check()


def start_background_check() -> None:
    global _thread
    _stop.clear()
    _thread = threading.Thread(target=_worker, name="updater-check", daemon=True)
    _thread.start()


def stop_background_check() -> None:
    _stop.set()
    if _thread is not None:
        _thread.join(timeout=3)


def available() -> UpdateInfo | None:
    """Lo que consultan los bucles de menú. `None` hasta que el hilo termine."""
    return _available


def _staging_dir() -> Path:
    from valeterna.config.paths import BASE_DIR

    return BASE_DIR / ".update"


def cleanup_staging() -> None:
    """Borra `BASE_DIR/.update/` (carpeta de trabajo de una actualización). Se
    llama al arrancar, para no dejar restos de un intento anterior."""
    shutil.rmtree(_staging_dir(), ignore_errors=True)


# --- Descarga, verificación y aplicación ---


def verify(zip_path: Path, info: UpdateInfo) -> bool:
    """Comprueba el SHA-256 del zip contra el publicado en el Release. Sin hash
    publicado, se niega a aplicar (hueco para una firma en el futuro)."""
    if not info.sha256:
        logger.warning("El Release %s no publica SHA256SUMS; no se aplica.", info.tag)
        return False
    h = hashlib.sha256()
    with open(zip_path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest().lower() == info.sha256.lower()


def _download(url: str, dest: Path, on_progress: Callable[[float], None] | None) -> None:  # pragma: no cover - red
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp, open(dest, "wb") as out:
        total = int(resp.headers.get("Content-Length") or 0)
        done = 0
        while chunk := resp.read(1 << 16):
            out.write(chunk)
            done += len(chunk)
            if on_progress and total:
                on_progress(done / total)


def download_and_stage(info: UpdateInfo, on_progress: Callable[[float], None] | None = None) -> Path | None:
    """Descarga el zip a `.update/`, verifica el SHA-256 y lo extrae. Devuelve la
    carpeta `Valeterna/` extraída, o `None` si algo falla (y limpia)."""
    staging = _staging_dir()
    shutil.rmtree(staging, ignore_errors=True)
    staging.mkdir(parents=True, exist_ok=True)
    zip_path = staging / "download.zip"
    try:
        _download(info.zip_url, zip_path, on_progress)
        if not verify(zip_path, info):
            logger.warning("La descarga no pasó la verificación SHA-256.")
            raise ValueError("verificación fallida")
        new_dir = staging / "new"
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(new_dir)
    except Exception as exc:  # noqa: BLE001 - el updater nunca debe lanzar
        logger.warning("No se pudo preparar la actualización: %s", exc)
        shutil.rmtree(staging, ignore_errors=True)
        return None

    inner = new_dir / "Valeterna"
    return inner if inner.is_dir() else None


_GAME_EXE = "Valeterna.exe"


def _apply_bat(pid: int) -> str:
    """Contenido del `.bat` relanzador (ASCII puro), escrito en `.update/`.

    `%~dp0` es la carpeta del `.bat` (`.update/`, con `\\` final); `HERE\\..`
    normalizado es la carpeta del juego. Todo tiene que funcionar en una consola
    nueva y sin depender del `cwd`:

    - la espera usa el **nombre del proceso** (`find /i`), no el PID a pelo
      (el PID podía colar como subcadena de otro dato de `tasklist`);
    - `ping` en vez de `timeout` como pausa (no necesita stdin);
    - `robocopy /MIR` (espeja: copia lo nuevo y **borra lo obsoleto**)
      protegiendo los datos del jugador con `/XD` y `/XF`. Sin ese borrado, el
      `*.dist-info` de la versión anterior quedaba junto al nuevo e
      `importlib.metadata` seguía devolviendo la versión vieja;
    - `/R:3 /W:2` para que un archivo bloqueado no lo cuelgue un millón de
      reintentos (el valor por defecto);
    - antes de espejar comprueba que `SRC` y `DST` contienen el `.exe` del
      juego (`/MIR` sobre la carpeta equivocada sería destructivo);
    - deja un `apply.log` al lado del `.bat` para diagnosticar.
    """
    return (
        "@echo off\r\n"
        "setlocal\r\n"
        "title Actualizando Valeterna\r\n"
        f'set "PID={pid}"\r\n'
        'set "HERE=%~dp0"\r\n'
        'for %%I in ("%HERE%..") do set "DST=%%~fI"\r\n'
        'set "SRC=%HERE%new\\Valeterna"\r\n'
        'set "LOG=%HERE%apply.log"\r\n'
        "echo Aplicando la actualizacion, espera unos segundos...\r\n"
        'echo [%date% %time%] inicio pid=%PID% SRC=%SRC% DST=%DST% > "%LOG%"\r\n'
        f'if not exist "%SRC%\\{_GAME_EXE}" goto badpaths\r\n'
        f'if not exist "%DST%\\{_GAME_EXE}" goto badpaths\r\n'
        "set /a n=0\r\n"
        ":wait\r\n"
        f'tasklist /fi "PID eq %PID%" /nh 2>nul | find /i "{_GAME_EXE}" >nul\r\n'
        "if errorlevel 1 goto copy\r\n"
        "set /a n+=1\r\n"
        "if %n% geq 60 goto copy\r\n"
        "ping -n 2 127.0.0.1 >nul\r\n"
        "goto wait\r\n"
        ":copy\r\n"
        'robocopy "%SRC%" "%DST%" /MIR /R:3 /W:2 /NFL /NDL /NJH /NJS /NP '
        '/XD "%DST%\\saved_games" "%DST%\\logs" "%DST%\\.update" '
        '/XF "%DST%\\config.ini" >> "%LOG%" 2>&1\r\n'
        'set "RC=%ERRORLEVEL%"\r\n'
        'echo [%date% %time%] robocopy RC=%RC% >> "%LOG%"\r\n'
        "if %RC% geq 8 (\r\n"
        "  echo.\r\n"
        "  echo ERROR: no se pudo aplicar la actualizacion ^(codigo %RC%^).\r\n"
        "  echo Detalles en: %LOG%\r\n"
        "  echo Abre el juego normalmente; se te volvera a ofrecer la actualizacion.\r\n"
        "  echo.\r\n"
        "  pause\r\n"
        "  exit /b 1\r\n"
        ")\r\n"
        'echo [%date% %time%] relanzando >> "%LOG%"\r\n'
        "ping -n 2 127.0.0.1 >nul\r\n"
        f'start "" /d "%DST%" "%DST%\\{_GAME_EXE}"\r\n'
        "exit /b 0\r\n"
        ":badpaths\r\n"
        'echo [%date% %time%] rutas invalidas SRC=%SRC% DST=%DST% >> "%LOG%"\r\n'
        "echo ERROR: no se encontro la carpeta del juego; actualiza manualmente.\r\n"
        "pause\r\n"
        "exit /b 1\r\n"
    )


def apply_and_restart(new_dir: Path) -> NoReturn:  # pragma: no cover - lanza proceso y sale
    """Escribe `apply.bat`, lo lanza totalmente desprendido del juego y cierra.
    El `.bat` espera a que el proceso muera, espeja la versión nueva y relanza
    `Valeterna.exe`."""
    bat = _staging_dir() / "apply.bat"
    bat.write_text(_apply_bat(os.getpid()), encoding="ascii")

    # `os.startfile` = ShellExecute: el shell arranca el .bat en su propia
    # consola y de forma completamente asíncrona, sin heredar handles ni
    # depender del ciclo de vida del juego. Lanzarlo con `subprocess.Popen` +
    # `CREATE_NEW_CONSOLE` justo mientras el juego se cerraba provocaba a veces
    # un 0xC0000142 (fallo al inicializar cmd.exe) — ver SECURITY/CHANGELOG.
    start_file = getattr(os, "startfile", None)
    if start_file is not None:
        start_file(str(bat))
    else:  # pragma: no cover - fallback fuera de Windows, que no debería ocurrir
        subprocess.Popen(
            ["cmd", "/c", str(bat)],
            creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0),
            close_fds=True,
        )

    # Damos un margen para que la consola del .bat termine de arrancar antes de
    # que el juego (y su teardown de pygame/colorama) se lleve el proceso.
    sys.stdout.flush()
    time.sleep(1.5)
    sys.exit(0)
