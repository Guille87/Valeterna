"""Procesado de estados alterados en el enemigo (espejo de Player), GDD §6.4."""

import pytest

from valeterna.characters.enemies.goblin import Goblin


@pytest.fixture
def goblin():
    g = Goblin()
    g.stats.armor = 0
    g.stats.magic_resist = 0
    return g


def test_apply_status_stacks_duration_and_respects_immunity(goblin):
    assert goblin.apply_status("veneno", 3) is True
    goblin.apply_status("veneno", 5)  # refresca al máximo
    assert next(e for e in goblin.status_effects if e["name"] == "veneno")["duration"] == 5

    type(goblin).IMMUNE_STATUSES = frozenset({"paralizado"})
    try:
        assert goblin.apply_status("paralizado", 3) is False
        assert not any(e["name"] == "paralizado" for e in goblin.status_effects)
    finally:
        type(goblin).IMMUNE_STATUSES = frozenset()


def test_on_turn_start_ticks_dot_damage(goblin):
    goblin.stats.max_health = 160
    goblin.stats.health = 160
    goblin.apply_status("veneno", 3)  # 160 // 8 = 20 / turno

    goblin.on_turn_start()
    assert goblin.stats.health == 140


def test_on_turn_start_paralysis_skips_the_turn(goblin, monkeypatch):
    monkeypatch.setattr("random.random", lambda: 0.0)  # < 0.5 -> pierde el turno
    goblin.apply_status("paralizado", 2)
    assert goblin.on_turn_start() is False


def test_frozen_enemy_skips_the_turn_but_can_thaw(goblin, monkeypatch):
    goblin.apply_status("congelado", 3)

    # 1er turno: siempre pierde el turno (no se tira el 20%), aunque random dé 0.
    monkeypatch.setattr("random.random", lambda: 0.0)
    assert goblin.on_turn_start() is False
    assert any(e["name"] == "congelado" for e in goblin.status_effects)

    # A partir del 2º: 20% de descongelarse.
    monkeypatch.setattr("random.random", lambda: 0.9)  # no se descongela
    assert goblin.on_turn_start() is False

    monkeypatch.setattr("random.random", lambda: 0.0)  # < 0.20 -> se descongela
    goblin.on_turn_start()
    assert not any(e["name"] == "congelado" for e in goblin.status_effects)


def test_burn_halves_the_enemy_physical_attack(goblin, monkeypatch):
    monkeypatch.setattr("random.randint", lambda a, b: 20)
    assert goblin.get_attack_damage() == 20
    goblin.apply_status("quemado", 3)
    assert goblin.get_attack_damage() == 10


def test_decay_removes_expired_effects(goblin):
    goblin.apply_status("veneno", 1)
    goblin.decay_status_effects()
    assert goblin.status_effects == []


def test_consagrado_blocks_self_heal_and_marchito_halves_it(goblin):
    goblin.stats.max_health = 100
    goblin.stats.health = 50

    goblin.apply_status("marchito", 3)
    assert goblin.heal(20) == 10  # -50 %
    goblin.status_effects.clear()

    goblin.stats.health = 50
    goblin.apply_status("consagrado", 3)
    assert goblin.heal(20) == 0  # bloqueado


def test_consagrado_makes_the_target_take_25_percent_more(goblin):
    goblin.apply_status("consagrado", 3)
    assert goblin.take_damage(100) == 125


def test_fractura_magica_zeroes_magic_resist(goblin):
    goblin.stats.magic_resist = 60
    assert goblin.take_damage(40, is_magical=True) == 10  # 40 * 20/(60+20)
    goblin.apply_status("fractura_magica", 3)
    assert goblin.take_damage(40, is_magical=True) == 40  # resistencia -> 0, daño íntegro
