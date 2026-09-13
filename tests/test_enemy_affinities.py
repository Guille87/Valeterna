"""Afinidades elementales reales de los 14 enemigos actuales (GDD §5, v0.11.0-a).

Cada caso fija la tabla de diseño acordada: débilidades/resistencias/inmunidades
por enemigo, y la regla "inmune al elemento -> también inmune al estado de ese
elemento" (necesaria porque al menos una vía de aplicación de estado, la pasiva
Veneno de Contacto en `_execute_turn`, llama a `apply_status` directamente sin
pasar por `affinity_for()` primero).
"""

import pytest

from valeterna.characters.enemies.angel_caido import AngelCaido
from valeterna.characters.enemies.bandido import Bandido
from valeterna.characters.enemies.demonio import Demonio
from valeterna.characters.enemies.dragon import Dragon
from valeterna.characters.enemies.espiritu_vengativo import EspirituVengativo
from valeterna.characters.enemies.gargola import Gargola
from valeterna.characters.enemies.goblin import Goblin
from valeterna.characters.enemies.golem import GolemDePiedra
from valeterna.characters.enemies.huargo import Huargo
from valeterna.characters.enemies.mage import Mago
from valeterna.characters.enemies.nigromante import Nigromante
from valeterna.characters.enemies.orc import Orc
from valeterna.characters.enemies.skeleton import Skeleton
from valeterna.characters.enemies.troll import Troll


@pytest.mark.parametrize("enemy_cls", [Goblin, Huargo])
def test_starter_enemies_are_elementally_neutral(enemy_cls):
    assert not enemy_cls.WEAKNESSES
    assert not enemy_cls.RESISTANCES
    assert not enemy_cls.IMMUNE_ELEMENTS
    assert not enemy_cls.IMMUNE_STATUSES


def test_skeleton_resists_poison_but_is_only_status_immune_to_it():
    skeleton = Skeleton()
    assert skeleton.affinity_for({"sagrado"}) == 1.5
    assert skeleton.affinity_for({"veneno"}) == 0.5  # resiste, no es inmune al elemento
    assert skeleton.resists_element("veneno") is True
    assert skeleton.is_immune_to_status("veneno") is True
    assert skeleton.is_immune_to_status("sangrado") is True
    assert skeleton.apply_status("veneno", 3) is False
    assert skeleton.apply_status("sangrado", 3) is False


def test_bandido_is_weak_to_poison():
    bandido = Bandido()
    assert bandido.affinity_for({"veneno"}) == 1.5


def test_orco_resists_poison_with_no_weakness():
    orco = Orc()
    assert not orco.WEAKNESSES
    assert orco.affinity_for({"veneno"}) == 0.5


def test_espiritu_vengativo_is_immune_to_poison_element_and_status():
    espiritu = EspirituVengativo()
    assert espiritu.affinity_for({"sagrado"}) == 1.5
    assert espiritu.affinity_for({"veneno"}) == 0.0
    assert espiritu.is_immune_to_status("veneno") is True
    assert espiritu.apply_status("veneno", 3) is False


def test_troll_is_weak_to_fire():
    troll = Troll()
    assert troll.affinity_for({"fuego"}) == 1.5


def test_gargola_is_immune_to_poison_element_and_status():
    gargola = Gargola()
    assert gargola.affinity_for({"arcano"}) == 1.5
    assert gargola.affinity_for({"veneno"}) == 0.0
    assert gargola.is_immune_to_status("veneno") is True
    assert gargola.apply_status("veneno", 3) is False


def test_golem_is_immune_to_lightning_element_and_paralysis_status():
    golem = GolemDePiedra()
    assert golem.affinity_for({"hielo"}) == 1.5
    assert golem.affinity_for({"rayo"}) == 0.0
    assert golem.is_immune_to_status("paralizado") is True
    assert golem.apply_status("paralizado", 3) is False


def test_mago_resists_arcane_with_no_elemental_weakness():
    mago = Mago()
    assert not mago.WEAKNESSES
    assert mago.affinity_for({"arcano"}) == 0.5


def test_nigromante_is_immune_to_darkness_element_and_withered_status():
    nigromante = Nigromante()
    assert nigromante.affinity_for({"sagrado"}) == 1.5
    assert nigromante.affinity_for({"oscuridad"}) == 0.0
    assert nigromante.is_immune_to_status("marchito") is True
    assert nigromante.apply_status("marchito", 3) is False


def test_angel_caido_is_weak_to_darkness_and_resists_holy():
    angel = AngelCaido()
    assert angel.affinity_for({"oscuridad"}) == 1.5
    assert angel.affinity_for({"sagrado"}) == 0.5


def test_demonio_is_weak_to_holy_and_only_resists_darkness():
    demonio = Demonio()
    assert demonio.affinity_for({"sagrado"}) == 1.5
    assert demonio.affinity_for({"oscuridad"}) == 0.5  # resiste, no inmune (a diferencia del Nigromante)
    assert demonio.is_immune_to_status("marchito") is False


def test_dragon_is_immune_to_fire_element_and_burn_status():
    dragon = Dragon()
    assert dragon.affinity_for({"hielo"}) == 1.5
    assert dragon.affinity_for({"fuego"}) == 0.0
    assert dragon.is_immune_to_status("quemado") is True
    assert dragon.apply_status("quemado", 3) is False
