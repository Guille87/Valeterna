"""Cimientos del paquete `world/` (GDD §3, §9.2, v0.12.0-a): datos de zona y
el grafo del mapa. Todavía no hay bucle de exploración; esto solo cubre los
datos y las ayudas de progreso usadas por la migración de guardado."""

from valeterna.combat.battle import ENEMY_PROGRESSION
from valeterna.world.map import ZONE_ORDER, ZONES, default_zone_for_progress, zone_for_enemy


def test_zone_order_matches_the_zones_registry():
    assert set(ZONE_ORDER) == set(ZONES)
    assert len(ZONE_ORDER) == len(ZONES)  # sin duplicados


def test_piedrablanca_is_the_hub_with_no_enemies():
    assert ZONE_ORDER[0] == "piedrablanca"
    assert ZONES["piedrablanca"].enemies == ()


def test_every_backbone_enemy_belongs_to_exactly_one_zone():
    backbone_enemies = set(ENEMY_PROGRESSION)  # las 14 claves = los 14 enemigos actuales
    assigned = set()
    for zone in ZONES.values():
        assert assigned.isdisjoint(zone.enemies)  # ninguno repetido en dos zonas
        assigned.update(zone.enemies)
    assert assigned == backbone_enemies


def test_zone_for_enemy_finds_the_right_zone():
    assert zone_for_enemy("Goblin") == "los_yermos"
    assert zone_for_enemy("Mago") == "torre_de_los_arcanos"
    assert zone_for_enemy("Dragón") == "corazon_de_la_brecha"


def test_zone_for_enemy_returns_none_for_an_unknown_name():
    assert zone_for_enemy("No Existe") is None


def test_default_zone_for_progress_with_no_defeats_is_the_hub():
    assert default_zone_for_progress([]) == "piedrablanca"


def test_default_zone_for_progress_advances_along_the_chain():
    assert default_zone_for_progress(["Goblin"]) == "los_yermos"
    assert default_zone_for_progress(["Goblin", "Huargo", "Esqueleto", "Bandido"]) == "los_yermos"
    assert default_zone_for_progress(["Goblin", "Orco"]) == "bosque_de_los_susurros"


def test_default_zone_for_progress_stops_at_the_first_zone_with_no_defeats():
    """Ciénaga de los Ahogados todavía no tiene roster (GDD §4): un progreso
    que la "salta" por completo no debe hacer que la zona actual avance de
    más allá de Cañón del Trueno."""
    defeated = ["Goblin", "Orco", "Gárgola"]  # Los Yermos, Bosque, Cañón — pero no Ciénaga (vacía)
    assert default_zone_for_progress(defeated) == "canon_del_trueno"
