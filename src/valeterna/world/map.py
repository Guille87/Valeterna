"""Grafo de zonas y ayudas de progreso (GDD §3, §9.2).

`next_zone()`/`is_zone_reachable()` alimentan el viaje real de
`ui/exploration.py::_travel_flow()` (v0.12.0-b); `default_zone_for_progress()`
solo la usa la migración de guardado v1 -> v2 (`persistence/save_load.py`,
v0.12.0-a).
"""

from valeterna.world.data import (
    bosque_de_los_susurros,
    canon_del_trueno,
    cienaga_de_los_ahogados,
    ciudadela_en_ruinas,
    corazon_de_la_brecha,
    los_yermos,
    piedrablanca,
    torre_de_los_arcanos,
)
from valeterna.world.npc import NPC
from valeterna.world.zone import Zone

# Orden de la cadena del mapa (GDD §3): Piedrablanca es el pueblo (sin
# enemigos), el resto sigue la ruta lineal actual del diseño.
ZONE_ORDER: tuple[str, ...] = (
    piedrablanca.ZONE.id,
    los_yermos.ZONE.id,
    bosque_de_los_susurros.ZONE.id,
    cienaga_de_los_ahogados.ZONE.id,
    canon_del_trueno.ZONE.id,
    torre_de_los_arcanos.ZONE.id,
    ciudadela_en_ruinas.ZONE.id,
    corazon_de_la_brecha.ZONE.id,
)

ZONES: dict[str, Zone] = {
    zone.id: zone
    for zone in (
        piedrablanca.ZONE,
        los_yermos.ZONE,
        bosque_de_los_susurros.ZONE,
        cienaga_de_los_ahogados.ZONE,
        canon_del_trueno.ZONE,
        torre_de_los_arcanos.ZONE,
        ciudadela_en_ruinas.ZONE,
        corazon_de_la_brecha.ZONE,
    )
}

# Todos los NPC del juego por id; cada módulo de zona aporta los suyos en un
# `NPCS` opcional (v0.13.0).
NPCS: dict[str, NPC] = {
    npc.id: npc
    for module in (
        piedrablanca,
        los_yermos,
        bosque_de_los_susurros,
        cienaga_de_los_ahogados,
        canon_del_trueno,
        torre_de_los_arcanos,
        ciudadela_en_ruinas,
        corazon_de_la_brecha,
    )
    for npc in getattr(module, "NPCS", ())
}


def npcs_in_zone(zone_id: str) -> list[NPC]:
    """Los NPC con los que se puede hablar en `zone_id`."""
    return [npc for npc in NPCS.values() if npc.zone_id == zone_id]


def zone_for_enemy(enemy_name: str) -> str | None:
    """La zona a la que pertenece un enemigo "backbone" ya implementado, o
    `None` si no está asignado a ninguna (no debería pasar con los 14
    actuales, pero un enemigo de diseño futuro aún sin zona no debe romper
    nada aquí)."""
    for zone in ZONES.values():
        if enemy_name in zone.enemies:
            return zone.id
    return None


def next_zone(zone_id: str) -> str | None:
    """La zona siguiente en `ZONE_ORDER` tras `zone_id` (la "frontera" a pie
    desde ahí), o `None` si `zone_id` es la última de la cadena."""
    idx = ZONE_ORDER.index(zone_id)
    if idx + 1 >= len(ZONE_ORDER):
        return None
    return ZONE_ORDER[idx + 1]


def is_zone_reachable(zone_id: str, unlocked_enemies: list) -> bool:
    """¿Se puede viajar ya a pie hasta `zone_id` (GDD §3, "frontera")? Una
    zona sin roster propio todavía (GDD §4, p. ej. Ciénaga de los Ahogados) no
    tiene nada que la bloquee: se considera siempre abierta. El resto, en
    cuanto su primer enemigo backbone está desbloqueado."""
    enemies = ZONES[zone_id].enemies
    if not enemies:
        return True
    return enemies[0] in unlocked_enemies


def default_zone_for_progress(defeated_enemies: list) -> str:
    """Zona por defecto para partidas guardadas antes del bloque `mundo`
    (migración v1 -> v2, GDD §9.4): la más avanzada de la cadena en la que ya
    se ha derrotado a algún enemigo backbone. Sin ningún progreso, Piedrablanca
    (el pueblo). Aproximación deliberada: todavía no hay guardianes que abran
    zonas "de verdad", así que se infiere del propio progreso de combate. Una
    zona todavía sin roster (p. ej. Ciénaga de los Ahogados, GDD §4) se salta
    sin cortar el avance — no bloquea llegar a la siguiente."""
    current = ZONE_ORDER[0]
    for zone_id in ZONE_ORDER[1:]:
        enemies = ZONES[zone_id].enemies
        if not enemies:
            continue
        if any(enemy in defeated_enemies for enemy in enemies):
            current = zone_id
        else:
            break
    return current
