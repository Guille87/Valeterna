import pygame
import pytest

from valeterna.audio import resource_manager as rm_mod
from valeterna.audio.resource_manager import ResourceManager


@pytest.fixture
def rm():
    """ResourceManager es un singleton: limpiamos su estado antes y después."""
    manager = ResourceManager()
    manager.sounds.clear()
    manager.music_paths.clear()
    manager.current_track_name = None
    manager.mood = "adventure"
    manager.target_enemy = None
    yield manager
    manager.sounds.clear()
    manager.music_paths.clear()
    manager.current_track_name = None


@pytest.fixture
def restore_mixer():
    """Algunos tests cierran el mezclador a propósito; lo reabrimos al terminar
    para no romper la fixture de audio de sesión que comparten los demás tests."""
    yield
    if not pygame.mixer.get_init():
        pygame.mixer.init()


def test_update_is_silent_when_mixer_is_closed(restore_mixer, capsys):
    """Regresión: al salir del juego el mezclador se cierra mientras el hilo de
    música en segundo plano puede dar una última vuelta. update()/play_music()
    no deben lanzar ni imprimir 'Audio device hasn't been opened'."""
    rm = ResourceManager()
    rm.music_paths.setdefault("ale_and_anecdotes", "no/importa/la/ruta.ogg")

    pygame.mixer.quit()
    assert not pygame.mixer.get_init()

    rm.update()
    rm.play_music("ale_and_anecdotes")

    assert "Audio device hasn't been opened" not in capsys.readouterr().out


def test_music_watchdog_stops_before_join():
    """El hilo de música debe salir de su bucle en cuanto se activa el evento
    de parada, para poder cerrar el mezclador sin carreras al salir del juego."""
    from valeterna import app

    app._music_watchdog_stop.clear()
    import threading

    t = threading.Thread(target=app._music_watchdog, daemon=True)
    t.start()
    app._music_watchdog_stop.set()
    t.join(timeout=5)

    assert not t.is_alive()
    app._music_watchdog_stop.clear()


# --- Selección de música ---


def test_play_battle_music_routes_by_enemy(rm, monkeypatch):
    calls = []
    monkeypatch.setattr(rm, "play_music", lambda name, loops=0: calls.append(name))
    monkeypatch.setattr(rm, "play_random_adventure_music", lambda: calls.append("adventure"))

    rm.play_battle_music("Dragón")
    rm.play_battle_music("Mago")  # enemigo duro
    rm.play_battle_music("Goblin")  # enemigo fácil -> pool de aventura

    assert calls == ["Siege_of_the_Black_Gate", "scaring_crows", "adventure"]


def test_enter_battle_switches_music_only_for_dedicated_enemies(rm, monkeypatch):
    calls = []
    monkeypatch.setattr(rm, "play_battle_music", lambda enemy: calls.append(enemy))

    rm.set_mood("adventure")
    rm.enter_battle("Goblin")  # estándar -> no toca la música
    assert calls == []
    assert rm.mood == "adventure"

    rm.enter_battle("Dragón")  # jefe -> cambia
    assert calls == ["Dragón"]
    assert rm.mood == "battle"


def test_exit_battle_only_forces_a_track_when_leaving_dedicated_music(rm, monkeypatch):
    calls = []
    monkeypatch.setattr(rm, "play_random_adventure_music", lambda: calls.append("adventure"))

    rm.set_mood("adventure")
    rm.exit_battle()  # no veníamos de combate -> no corta nada
    assert calls == []

    rm.set_mood("battle", "Mago")
    rm.exit_battle()
    assert calls == ["adventure"]
    assert rm.mood == "adventure"


def test_play_random_adventure_music_picks_from_the_pool(rm, monkeypatch):
    monkeypatch.setattr(rm_mod.random, "choice", lambda seq: seq[0])
    played = []
    monkeypatch.setattr(rm, "play_music", lambda name, loops=0: played.append(name))

    rm.play_random_adventure_music()
    assert played == ["a_robust_crew"]


def test_update_routes_by_mood(rm, monkeypatch):
    monkeypatch.setattr("pygame.mixer.music.get_busy", lambda: False)
    calls = []
    monkeypatch.setattr(rm, "play_battle_music", lambda enemy: calls.append(("battle", enemy)))
    monkeypatch.setattr(rm, "play_random_adventure_music", lambda: calls.append(("adventure",)))

    rm.set_mood("battle", "Orco")
    rm.update()
    rm.set_mood("adventure")
    rm.update()

    assert calls == [("battle", "Orco"), ("adventure",)]


# --- Carga y reproducción ---


def test_load_audio_stores_music_path_and_loads_sfx(rm, monkeypatch, tmp_path):
    fake_file = tmp_path / "x.ogg"
    fake_file.write_bytes(b"0")

    rm.load_audio("tema", str(fake_file), is_music=True)
    assert rm.music_paths["tema"] == str(fake_file)

    real_sound = pygame.mixer.Sound(buffer=b"\x00" * 44)
    monkeypatch.setattr("pygame.mixer.Sound", lambda path: real_sound)
    rm.load_audio("golpe", str(fake_file), is_music=False)
    assert "golpe" in rm.sounds


def test_play_music_loads_and_remembers_the_track(rm, monkeypatch):
    rm.music_paths["tema"] = "ruta/tema.ogg"
    monkeypatch.setattr("pygame.mixer.music.load", lambda path: None)
    monkeypatch.setattr("pygame.mixer.music.set_volume", lambda v: None)
    monkeypatch.setattr("pygame.mixer.music.play", lambda loops=0: None)
    monkeypatch.setattr("pygame.mixer.music.get_busy", lambda: False)

    rm.play_music("tema")
    assert rm.current_track_name == "tema"


def test_play_music_does_nothing_for_unknown_track(rm):
    rm.play_music("no-existe")
    assert rm.current_track_name is None


def test_play_sfx_plays_known_and_warns_on_unknown(rm, capsys):
    sound = pygame.mixer.Sound(buffer=b"\x00" * 44)
    rm.sounds["golpe"] = sound
    rm.play_sfx("golpe")  # sin excepción

    rm.play_sfx("desconocido")
    assert "no encontrado" in capsys.readouterr().out


def test_volume_setters(rm):
    rm.set_volume_music(0.3)
    rm.set_volume_sfx(0.6)
    assert rm.current_volume_music == 0.3
    assert rm.current_volume_sfx == 0.6


def test_stop_all_music_clears_current_track(rm, monkeypatch):
    monkeypatch.setattr("pygame.mixer.music.stop", lambda: None)
    rm.current_track_name = "algo"
    rm.stop_all_music()
    assert rm.current_track_name is None
