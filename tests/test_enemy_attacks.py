"""Ataques básicos y de rutina de Bandido, Ángel Caído, Demonio y Dragón
(los efectos de estado y las ramas de invocación/curación ya están en
test_new_enemies.py; aquí se cubren los zarpazos y las ramas de fallo)."""

import pytest

from valeterna.characters.enemies.angel_caido import AngelCaido
from valeterna.characters.enemies.bandido import Bandido
from valeterna.characters.enemies.demonio import Demonio
from valeterna.characters.enemies.dragon import Dragon


@pytest.fixture
def hit(monkeypatch):
    monkeypatch.setattr("random.random", lambda: 0.0)
    monkeypatch.setattr("random.randint", lambda a, b: 20)


@pytest.fixture
def miss(monkeypatch):
    monkeypatch.setattr("random.random", lambda: 0.99)


def test_bandido_ambush_hits_once(player, hit):
    player.stats.armor = 0
    bandido = Bandido()
    before = player.stats.health

    assert bandido.check_ambush(player) is True
    assert player.stats.health < before
    assert bandido.check_ambush(player) is False


def test_bandido_disarm_can_miss(player, miss):
    player.stats.evasion = 500
    Bandido()._attempt_disarm(player)
    assert not any(e["name"] == "desarmado" for e in player.status_effects)


def test_bandido_perform_turn_routes_to_disarm(player, monkeypatch):
    monkeypatch.setattr("random.random", lambda: 0.0)  # < 0.25 -> desarme
    player.stats.evasion = 0
    Bandido().perform_turn(player)
    assert any(e["name"] == "desarmado" for e in player.status_effects)


def test_dragon_claw_attack_hits_and_can_be_dodged(player, hit, monkeypatch):
    player.stats.armor = 0
    player.stats.evasion = 0
    dragon = Dragon()
    before = player.stats.health
    dragon._claw_attack(player)
    assert player.stats.health < before

    player.stats.evasion = 500
    monkeypatch.setattr("random.random", lambda: 0.99)
    steady = player.stats.health
    dragon._claw_attack(player)
    assert player.stats.health == steady


def test_dragon_perform_turn_uses_claw_most_of_the_time(player, monkeypatch):
    monkeypatch.setattr("random.random", lambda: 0.99)  # >= 0.25 -> zarpazo
    player.stats.evasion = 0
    player.stats.armor = 0
    dragon = Dragon()
    before = player.stats.health
    dragon.perform_turn(player)
    assert player.stats.health < before


def test_demonio_claw_and_summon_deal_damage(player, hit):
    player.stats.armor = 0
    player.stats.magic_resist = 0
    player.stats.evasion = 0
    demonio = Demonio()

    before = player.stats.health
    demonio._claw_attack(player)
    assert player.stats.health < before

    player.stats.health = player.stats.max_health  # el zarpazo crítico (v0.14.0-c: siempre max_atk) puede dejarlo a 0
    before = player.stats.health
    demonio._summon_lesser_demon(player)
    assert player.stats.health < before


def test_angel_caido_holy_strike_hits_and_misses(player, hit, monkeypatch):
    player.stats.magic_resist = 0
    player.stats.evasion = 0
    angel = AngelCaido()
    before = player.stats.health
    angel._holy_strike(player)
    assert player.stats.health < before

    player.stats.evasion = 500
    monkeypatch.setattr("random.random", lambda: 0.99)
    steady = player.stats.health
    angel._holy_strike(player)
    assert player.stats.health == steady


@pytest.mark.parametrize("enemy_cls", [Bandido, AngelCaido, Demonio, Dragon])
def test_drop_item_returns_a_list(monkeypatch, enemy_cls):
    monkeypatch.setattr("random.random", lambda: 0.0)
    drops = enemy_cls().drop_item()
    assert isinstance(drops, list) and len(drops) >= 1
