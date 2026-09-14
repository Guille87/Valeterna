"""Reacciones elementales (v0.11.0-c, GDD §5):

- "Fusión": un golpe de rayo contra un objetivo congelado rompe el hielo al
  instante y hace daño extra, en vez del paralizado normal del rayo.
- "Combustión": quemado + veneno (en cualquier orden) se funden en un único
  estado más dañino que cualquiera de los dos por separado.
"""

import re

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.enemies.mage import Mago
from valeterna.characters.enemies.skeleton import Skeleton
from valeterna.characters.stats import Stats
from valeterna.combat.battle import _execute_turn
from valeterna.items.equipment import Weapon


def _bare_enemy(**overrides) -> Enemy:
    stats = Stats(health=1000, max_health=1000, min_atk=5, max_atk=5, armor=0, magic_resist=0)
    for key, value in overrides.items():
        setattr(stats, key, value)
    return Enemy("Muñeco de pruebas", stats, gold_min=0, gold_max=0)


# --- Fusión: rayo + congelado ------------------------------------------------


def test_enemy_shatter_removes_freeze_and_boosts_damage():
    enemy = _bare_enemy()
    enemy.apply_status("congelado", 3)

    dmg = enemy.take_damage(20, element="rayo")

    assert dmg == 30  # 20 * 1.5 (armadura 0 no reduce nada)
    assert enemy.just_shattered is True
    assert not any(e["name"] == "congelado" for e in enemy.status_effects)


def test_enemy_no_shatter_without_freeze():
    enemy = _bare_enemy()

    dmg = enemy.take_damage(20, element="rayo")

    assert dmg == 20
    assert enemy.just_shattered is False


def test_enemy_no_shatter_for_other_elements_even_if_frozen():
    enemy = _bare_enemy()
    enemy.apply_status("congelado", 3)

    dmg = enemy.take_damage(20, element="fuego")

    assert dmg == 20
    assert enemy.just_shattered is False
    assert any(e["name"] == "congelado" for e in enemy.status_effects)


def test_player_shatter_removes_freeze_and_boosts_damage(player):
    player.stats.armor = 0
    player.apply_status("congelado", 3)

    dmg = player.take_damage(20, element="rayo")

    assert dmg == 30
    assert player.just_shattered is True
    assert not any(e["name"] == "congelado" for e in player.status_effects)


def test_mage_thunder_skips_paralysis_after_shattering_the_player(player, monkeypatch):
    player.apply_status("congelado", 3)
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)  # acierta, sin crítico
    monkeypatch.setattr("valeterna.characters.enemies.mage.random.randint", lambda a, b: 10)
    monkeypatch.setattr(
        "valeterna.characters.enemies.mage.random.random", lambda: 0.0
    )  # forzaría paralizar si se intentase

    Mago()._cast_thunder(player)

    assert player.just_shattered is True
    assert not any(e["name"] == "paralizado" for e in player.status_effects)


def test_weapon_shatter_hit_does_not_also_inflict_paralysis(player, weak_enemy, monkeypatch):
    weak_enemy.stats.health = 1000
    weak_enemy.stats.max_health = 1000
    weak_enemy.apply_status("congelado", 3)
    player.equipped_weapon = Weapon("Garra de Tormenta", "desc", 0, damage=15, element="rayo")
    monkeypatch.setattr("valeterna.combat.battle.random.random", lambda: 0.0)  # golpe crítico y toda tirada favorable
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)  # siempre acierta

    _execute_turn(player, weak_enemy, defeated_enemies=[])

    assert weak_enemy.just_shattered is True
    assert not any(e["name"] == "paralizado" for e in weak_enemy.status_effects)


# --- Combustión: quemado + veneno --------------------------------------------


def test_enemy_burn_then_poison_merges_into_combustion():
    enemy = _bare_enemy()
    enemy.apply_status("quemado", 2)

    applied = enemy.apply_status("veneno", 4)

    assert applied is True
    names = [e["name"] for e in enemy.status_effects]
    assert names == ["combustion"]
    assert enemy.status_effects[0]["duration"] == 4  # max(2, 4)


def test_enemy_poison_then_burn_merges_into_combustion_too():
    enemy = _bare_enemy()
    enemy.apply_status("veneno", 5)

    enemy.apply_status("quemado", 2)

    names = [e["name"] for e in enemy.status_effects]
    assert names == ["combustion"]
    assert enemy.status_effects[0]["duration"] == 5  # max(5, 2)


def test_enemy_immune_to_poison_status_never_reaches_combustion():
    skeleton = Skeleton()
    skeleton.apply_status("quemado", 3)

    applied = skeleton.apply_status("veneno", 3)

    assert applied is False
    names = [e["name"] for e in skeleton.status_effects]
    assert names == ["quemado"]


def test_enemy_combustion_deals_more_damage_than_burn_or_poison_alone():
    enemy = _bare_enemy()
    enemy.apply_status("quemado", 2)
    enemy.apply_status("veneno", 2)
    health_before = enemy.stats.health

    enemy.on_turn_start()

    combustion_dmg = health_before - enemy.stats.health
    burn_only = max(1, 1000 // 16)
    poison_only = max(1, 1000 // 8)
    assert combustion_dmg > burn_only
    assert combustion_dmg > poison_only


def test_enemy_combustion_halves_physical_attack_like_burn():
    enemy = _bare_enemy(min_atk=10, max_atk=10)
    enemy.apply_status("quemado", 2)
    enemy.apply_status("veneno", 2)

    assert enemy.get_attack_damage() == 5


def test_player_burn_then_poison_merges_into_combustion(player):
    player.apply_status("quemado", 2)

    player.apply_status("veneno", 4)

    names = [e["name"] for e in player.status_effects]
    assert names == ["combustion"]
    assert player.status_effects[0]["duration"] == 4


def test_player_combustion_deals_more_damage_than_burn_or_poison_alone(player):
    player.apply_status("quemado", 2)
    player.apply_status("veneno", 2)
    health_before = player.stats.health

    player.on_turn_start()

    combustion_dmg = health_before - player.stats.health
    burn_only = max(1, player.stats.max_health // 16)
    poison_only = max(1, player.stats.max_health // 8)
    assert combustion_dmg > burn_only
    assert combustion_dmg > poison_only


def test_pop_status_reaction_message_is_none_without_a_reaction():
    enemy = _bare_enemy()
    enemy.apply_status("quemado", 2)

    assert enemy.pop_status_reaction_message() is None


def test_pop_status_reaction_message_returns_once_and_clears():
    enemy = _bare_enemy()
    enemy.apply_status("quemado", 2)
    enemy.apply_status("veneno", 2)

    msg = enemy.pop_status_reaction_message()

    assert msg is not None
    assert "combusti" in msg.lower()
    assert enemy.pop_status_reaction_message() is None  # ya se consumió


def test_enemy_combustion_blocks_further_burn_or_poison_without_refreshing_duration():
    enemy = _bare_enemy()
    enemy.apply_status("quemado", 2)
    enemy.apply_status("veneno", 2)  # -> combustion, duración 2

    applied = enemy.apply_status("veneno", 10)

    assert applied is False
    assert enemy.status_effects == [{"name": "combustion", "duration": 2, "power": 0, "fresh": True}]
    assert enemy.pop_status_reaction_message() is None  # no se repite el aviso


def test_player_combustion_blocks_further_burn_or_poison_without_refreshing_duration(player):
    player.apply_status("quemado", 2)
    player.apply_status("veneno", 2)

    player.apply_status("quemado", 10)

    assert player.status_effects == [{"name": "combustion", "duration": 2, "power": 0, "fresh": True}]
    assert player.pop_status_reaction_message() is None


def test_weapon_inflicted_burn_message_prints_before_the_combustion_message(player, weak_enemy, monkeypatch):
    """El usuario pidió que el mensaje "ha sido quemado" salga antes que el de
    fusión en combustión, no al revés."""
    weak_enemy.stats.health = 1000
    weak_enemy.stats.max_health = 1000
    weak_enemy.apply_status("veneno", 3)
    player.equipped_weapon = Weapon("Espada Flamígera", "desc", 0, damage=15, element="fuego")
    monkeypatch.setattr("valeterna.combat.battle.random.random", lambda: 0.0)
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)

    printed: list[str] = []
    monkeypatch.setattr("builtins.print", lambda *a, **k: printed.append(" ".join(str(x) for x in a)))

    _execute_turn(player, weak_enemy, defeated_enemies=[])

    stripped = [re.sub(r"\x1b\[[0-9;]*m", "", line) for line in printed]
    burn_idx = next(i for i, line in enumerate(stripped) if "ha sido quemado" in line)
    combustion_idx = next(i for i, line in enumerate(stripped) if "combusti" in line.lower())
    assert burn_idx < combustion_idx
