from valeterna.combat.battle import ENEMY_PROGRESSION
from valeterna.items.equipment import Weapon
from valeterna.ui.menus import _get_enemy_instance
from valeterna.world.map import ZONES, zone_for_enemy

# Excepciones deliberadas: un arma de un tier más bajo, DENTRO DE LA MISMA ZONA
# y del mismo elemento, con menos daño que una de un tier más alto. A
# diferencia de tests/test_armor_progression.py (que compara a lo largo de
# TODA la cadena), aquí solo se compara dentro de zona — el propio diseño ya
# reinicia el poder de cada zona más abajo (ver characters/power_budget.py),
# así que el arma con la que abre una zona nueva siendo más floja que la que
# cerraba la zona anterior no es una inversión real, es el mismo reinicio de
# la curva. Ver TODO.md, sección "revisión completa de los drops...".
KNOWN_EXCEPTIONS: set[tuple[str, str, str | None]] = set()


def _all_weapon_drops():
    """(zona_id, tier, nombre, Weapon) por cada arma que puede soltar cada enemigo."""
    for name in ENEMY_PROGRESSION:
        zone_id = zone_for_enemy(name)
        if zone_id is None:
            continue
        zone = ZONES[zone_id]
        tier = zone.enemies.index(name) + 1 if name in zone.enemies else None
        enemy = _get_enemy_instance(name)
        for item, _prob in enemy.drop_table():
            if isinstance(item, Weapon):
                yield zone_id, tier, name, item


def test_every_weapon_drop_deals_positive_damage():
    for _zone_id, _tier, name, item in _all_weapon_drops():
        assert item.damage > 0, f"{item.name} ({name}) no hace daño"


def test_weapon_damage_does_not_decrease_within_the_same_zone_and_element():
    """Dentro de una misma zona, un arma del mismo elemento (incluido "sin
    elemento" = arma física normal) no debería hacer menos daño que la de un
    tier más bajo de esa misma zona, salvo una excepción deliberada y
    documentada."""
    last_damage_by_zone_element: dict[tuple[str, str | None], tuple[int, str]] = {}
    drops = sorted(_all_weapon_drops(), key=lambda t: (t[0], t[1] if t[1] is not None else 0))
    for zone_id, _tier, name, item in drops:
        key = (zone_id, item.element)
        previous = last_damage_by_zone_element.get(key)
        if previous is not None and (name, zone_id, item.element) not in KNOWN_EXCEPTIONS:
            prev_damage, prev_name = previous
            assert item.damage >= prev_damage, (
                f"{item.name} ({name}, zona {zone_id}, elemento {item.element}) hace {item.damage} de daño, "
                f"menos que {prev_name} de un tier más bajo de la misma zona ({prev_damage})"
            )
        last_damage_by_zone_element[key] = (item.damage, name)
