"""Tests de `use()` de las pociones (las de combate dependen de `player.in_combat`)."""

from valeterna.items.potions.antidote_potion import AntidotePotion
from valeterna.items.potions.buff_potion import StatBuffPotion
from valeterna.items.potions.healing_potion import HealingPotion
from valeterna.items.potions.regen_potion import RegenPotion


def test_healing_potion_restores_health(player):
    player.stats.health = 10
    assert HealingPotion("Poción de Salud", "desc", 2, 20).use(player) is True
    assert player.stats.health == 30


def test_regen_potion_needs_combat(player):
    potion = RegenPotion("Poción de Regeneración", "desc", 8, regen_amount=10, duration=3)

    player.in_combat = False
    assert potion.use(player) is False

    player.in_combat = True
    assert potion.use(player) is True
    assert any(e["name"] == "regeneración" for e in player.status_effects)


def test_buff_potion_needs_combat_and_applies_the_boost(player):
    potion = StatBuffPotion("Poción de Fuerza", "desc", 5, stat_name="max_atk", boost=5, duration=3)
    base = player.stats.max_atk

    player.in_combat = False
    assert potion.use(player) is False
    assert player.stats.max_atk == base

    player.in_combat = True
    assert potion.use(player) is True
    assert player.stats.max_atk == base + 5
    assert potion in player.active_effects


def test_antidote_removes_debuffs_and_leaves_the_rest(player):
    player.apply_status("veneno", 3)
    player.apply_status("quemado", 2)
    player.apply_status("maldicion", 3, power=4)  # no curable

    assert AntidotePotion("Antídoto", "desc", 6).use(player) is True

    names = {e["name"] for e in player.status_effects}
    assert names == {"maldicion"}


def test_antidote_fails_when_there_is_nothing_to_cure(player):
    assert AntidotePotion("Antídoto", "desc", 6).use(player) is False
    player.apply_status("confusion", 3, power=5)  # tampoco es curable por el antídoto
    assert AntidotePotion("Antídoto", "desc", 6).use(player) is False


def test_buff_potion_remove_reverts_the_boost(player):
    potion = StatBuffPotion("Poción de Fuerza", "desc", 5, stat_name="max_atk", boost=5, duration=3)
    player.in_combat = True
    potion.use(player)
    boosted = player.stats.max_atk

    potion.remove(player)
    assert player.stats.max_atk == boosted - 5
