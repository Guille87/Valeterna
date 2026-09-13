"""Genera docs/screenshot.svg: captura un combate real (con sus colores ANSI) y
lo renderiza como una "ventana de terminal" en SVG.

    python tools/capture_screenshot.py

Requiere `pip install ansitoimg` (no es dependencia del juego). Reproducible:
usa una semilla fija para `random`.
"""

import io
import os
import random
import sys
from pathlib import Path

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import colorama
from ansitoimg import ansiToSVG

from valeterna.audio.resource_manager import ResourceManager
from valeterna.characters.enemies.goblin import Goblin
from valeterna.characters.player import Player
from valeterna.characters.stats import Stats
from valeterna.combat import battle
from valeterna.ui import console

REPO = Path(__file__).resolve().parents[1]


def _one_battle(seed: int) -> str:
    random.seed(seed)
    console.ask = lambda _prompt: "1"  # atacar siempre, y saltar los "Pulsa Enter"
    battle.time.sleep = lambda *_a, **_k: None
    ResourceManager.play_sfx = lambda *_a, **_k: None  # sin "SFX no encontrado" en el transcript

    player = Player("Guille", Stats(150, 150, 16, 24, 5, crit_chance=0.35))
    goblin = Goblin()
    goblin.ambush_done = True  # sin emboscada aleatoria, para un transcript limpio

    buf = io.StringIO()
    real_stdout = sys.stdout
    sys.stdout = buf
    try:
        battle.initiate_battle(player, goblin, defeated_enemies=["Goblin"], unlocked_enemies=["Goblin", "Huargo"])
    finally:
        sys.stdout = real_stdout
    return buf.getvalue()


def _capture_battle() -> str:
    colorama.init(strip=False, convert=False)  # queremos el ANSI crudo, no la conversión Win32
    # Buscamos un combate corto que enseñe un crítico y la subida de nivel.
    best = ""
    for seed in range(1000):
        txt = _one_battle(seed)
        if "crítico" in txt and "NIVEL" in txt and txt.count("\n") <= 34:
            return txt
        if "NIVEL" in txt and (not best or txt.count("\n") < best.count("\n")):
            best = txt
    return best


def main() -> None:
    ansi = _capture_battle()
    (REPO / "docs" / "screenshot.ansi").write_text(ansi, encoding="utf-8")
    out = REPO / "docs" / "screenshot.svg"
    ansiToSVG(ansi, str(out), width=66, title="Juego de Rol por Turnos")
    print(f"Escrito {out} ({out.stat().st_size} bytes, {ansi.count(chr(10))} líneas)")


if __name__ == "__main__":
    main()
