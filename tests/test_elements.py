"""Modelo de afinidades elementales (GDD §5)."""

import pytest

from valeterna.characters.enemies.goblin import Goblin
from valeterna.characters.enemies.troll import Troll
from valeterna.combat.elements import (
    ELEMENT_STATUS,
    MAGICAL_ELEMENTS,
    affinity_multiplier,
    is_magical_element,
)


def _mult(elements, weak=(), resist=(), immune=()):
    return affinity_multiplier(
        set(elements), weaknesses=set(weak), resistances=set(resist), immune_elements=set(immune)
    )


@pytest.mark.parametrize(
    ("elements", "weak", "resist", "immune", "expected"),
    [
        ({"fuego"}, (), (), (), 1.0),  # neutral
        ({"fuego"}, ("fuego",), (), (), 1.5),  # débil a uno -> x1.5
        ({"fuego", "hielo"}, ("fuego", "hielo"), (), (), 2.0),  # combina dos debilidades -> x2
        ({"fuego"}, (), ("fuego",), (), 0.5),  # resistente -> x0.5
        ({"fuego", "hielo"}, (), ("fuego", "hielo"), (), 0.25),  # dos resistencias combinadas -> x0.25
        ({"veneno"}, (), (), ("veneno",), 0.0),  # inmune -> x0
        ({"fuego"}, ("fuego",), ("fuego",), (), 0.75),  # débil y resistente al mismo -> se multiplican
        (set(), ("fuego",), (), (), 1.0),  # sin elemento -> neutral
        ({None}, ("fuego",), (), (), 1.0),  # None se ignora
    ],
)
def test_affinity_multiplier(elements, weak, resist, immune, expected):
    assert _mult(elements, weak, resist, immune) == expected


def test_magical_elements_are_flagged():
    assert is_magical_element("arcano") is True
    assert is_magical_element("fuego") is False
    assert is_magical_element(None) is False
    assert sorted(MAGICAL_ELEMENTS) == ["arcano", "oscuridad", "sagrado"]


def test_every_element_has_a_status():
    assert set(ELEMENT_STATUS) == {"fuego", "veneno", "rayo", "hielo", "sagrado", "oscuridad", "arcano"}


def test_enemy_affinity_uses_declared_weaknesses():
    troll = Troll()
    assert troll.affinity_for({"fuego"}) == 1.5
    assert troll.affinity_for({"hielo"}) == 1.0
    assert troll.resists_element("fuego") is False


def test_enemy_take_damage_applies_the_affinity_multiplier():
    troll = Troll()
    troll.stats.armor = 0
    normal = Troll()
    normal.stats.armor = 0

    assert troll.take_damage(20, element="fuego") == round(normal.take_damage(20) * 1.5)


def test_goblin_is_neutral_to_everything_by_default():
    goblin = Goblin()
    assert goblin.affinity_for({"fuego"}) == 1.0
    assert goblin.affinity_for({"arcano"}) == 1.0
