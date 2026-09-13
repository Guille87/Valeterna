import os

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")  # pygame.init() sin pantalla (CI/headless)

import pygame
import pytest

from valeterna.characters.enemies.goblin import Goblin
from valeterna.characters.player import Player
from valeterna.characters.stats import Stats


@pytest.fixture(scope="session", autouse=True)
def _headless_audio():
    """Inicializa pygame.mixer con el driver 'dummy' para poder correr ResourceManager sin audio real."""
    pygame.mixer.init()
    yield
    pygame.mixer.quit()


@pytest.fixture
def tmp_save_dir(tmp_path, monkeypatch):
    """Redirige el guardado de partidas a un directorio temporal."""
    from valeterna.persistence import save_load

    monkeypatch.setattr(save_load, "SAVE_DIR", tmp_path)
    return tmp_path


@pytest.fixture
def player() -> Player:
    return Player("Heroe", Stats(health=100, max_health=100, min_atk=5, max_atk=10, armor=2))


@pytest.fixture
def weak_enemy() -> Goblin:
    """Goblin con vida ínfima para forzar victorias deterministas en tests de combate."""
    goblin = Goblin()
    goblin.stats.health = 1
    goblin.stats.max_health = 1
    goblin.ambush_done = True  # Evita la emboscada aleatoria de inicio de combate
    return goblin
