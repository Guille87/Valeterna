"""Paquete `world/` (GDD §3, §9.2): datos de zona y el grafo del mapa —
registro de zonas, a qué zona pertenece cada enemigo, inferencia de progreso
para la migración de guardado (v0.12.0-a) y alcanzabilidad de zonas para viajar
(v0.12.0-b, usado por `ui/exploration.py::_travel_flow`)."""

from valeterna.combat.battle import ENEMY_PROGRESSION
from valeterna.world.map import (
    ZONE_ORDER,
    ZONES,
    default_zone_for_progress,
    is_zone_reachable,
    next_zone,
    zone_for_enemy,
)


def test_zone_order_matches_the_zones_registry():
    assert set(ZONE_ORDER) == set(ZONES)
    assert len(ZONE_ORDER) == len(ZONES)  # sin duplicados


def test_piedrablanca_is_the_hub_with_no_enemies():
    assert ZONE_ORDER[0] == "piedrablanca"
    assert ZONES["piedrablanca"].enemies == ()
    assert ZONES["piedrablanca"].is_hub is True


def test_only_piedrablanca_is_a_hub():
    """`is_hub` distingue "sin combate por diseño" (Piedrablanca) de "roster
    todavía sin diseñar" (p. ej. la Ciénaga, que sigue sin `is_hub`)."""
    hubs = [zid for zid, zone in ZONES.items() if zone.is_hub]
    assert hubs == ["piedrablanca"]


def test_every_backbone_enemy_belongs_to_exactly_one_zone():
    backbone_enemies = set(ENEMY_PROGRESSION)  # las 20 claves = los 20 enemigos actuales
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


def test_next_zone_follows_the_chain():
    assert next_zone("piedrablanca") == "los_yermos"
    assert next_zone("los_yermos") == "bosque_de_los_susurros"


def test_next_zone_is_none_after_the_last_zone():
    assert next_zone("corazon_de_la_brecha") is None


def test_zone_with_no_roster_is_always_reachable():
    assert is_zone_reachable("cienaga_de_los_ahogados", []) is True


def test_zone_reachable_once_its_first_enemy_is_unlocked():
    assert is_zone_reachable("los_yermos", []) is False
    assert is_zone_reachable("los_yermos", ["Goblin"]) is True
