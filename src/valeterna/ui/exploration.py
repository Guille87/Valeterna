"""Bucle de exploración por zona (GDD §8.1, v0.12.0-b/c): sustituye al antiguo
menú plano de `game_loop`. Igual que `ui/menus.py`, esto es casi todo
`input()`/`print()` encadenados (`omit`ido de la cobertura, ver
pyproject.toml) — la lógica no interactiva de verdad (tiradas de Explorar,
alcanzabilidad de zonas) vive en `world/map.py` y sí está testeada.

Importa de `ui.menus` solo dentro de las funciones (no a nivel de módulo)
para evitar un ciclo: `menus.py` llama a `zone_loop()` desde
`start_new_game()`/`load_saved_game()`, así que no puede importar este módulo
a nivel de módulo si este a su vez importase `menus` arriba del todo.
"""

import random
import sys

from valeterna import __version__
from valeterna.audio.resource_manager import ResourceManager
from valeterna.combat.battle import initiate_battle
from valeterna.ui import console
from valeterna.world.map import ZONES, is_zone_reachable, next_zone

resource_manager = ResourceManager()

# Pesos de la tirada de "Explorar" (GDD §8.1). El resto (0.20) es "no
# encuentras nada".
_EXPLORE_ENCOUNTER_CHANCE = 0.65
_EXPLORE_DISCOVERY_CHANCE = 0.15

# Dentro de la rama de hallazgo: probabilidad de que sea una poción en vez de
# oro (v0.12.0-c, GDD §8.1 "descubrimientos").
_DISCOVERY_POTION_CHANCE = 0.4

# Coste de descansar en la posada (GDD §7.4): provisional, sin ajustar contra
# los ingresos reales de oro todavía (era una "Open question" del GDD).
_REST_COST_PER_LEVEL = 10


def zone_loop(player, unlocked_enemies: list, defeated_enemies: list, is_admin: bool = False) -> None:
    """Bucle principal de la estancia en el mundo, ahora por zona en vez de
    un menú plano único."""
    from valeterna.ui.menus import _maybe_show_update_notice

    _maybe_show_update_notice(in_game=True)

    while True:
        resource_manager.update()  # Por si la pista de aventura ya ha terminado
        zone = ZONES[player.mundo["zona_actual"]]

        print("\n" + "=" * 40)
        print(console.colorize(f"ESTADO: {player.name} | Nivel: {player.level}", console.Fore.CYAN))
        print(console.colorize(f"Zona: {zone.name}", console.Fore.GREEN))
        print(console.colorize(f"v{__version__}", console.Fore.BLACK, bright=True))
        print("=" * 40)

        labels = ["Explorar", "Ir a...", "Viajar", "Personaje"]
        for i, label in enumerate(labels, 1):
            print(f"{i}. {label}")

        choice = console.ask(f"\nElige (1-{len(labels)}): ")
        if not choice.isdigit() or not (1 <= int(choice) <= len(labels)):
            console.error("Opción no válida.")
            continue

        idx = int(choice)
        if idx == 1:
            _explore(player, unlocked_enemies, defeated_enemies)
        elif idx == 2:
            _sublocation_flow(player, zone)
        elif idx == 3:
            _travel_flow(player, unlocked_enemies)
        elif idx == 4 and _character_menu(player, unlocked_enemies, defeated_enemies, is_admin) == "volver_menu":
            break


def _explore(player, unlocked_enemies: list, defeated_enemies: list) -> None:
    """Tirada ponderada (GDD §8.1): combate / hallazgo / nada. El combate
    elige al azar entre los enemigos desbloqueados de la zona actual; si
    ninguno de los backbone de la zona está entre los desbloqueados (p. ej.
    una zona sin roster todavía, como la Ciénaga), cae a cualquier enemigo
    desbloqueado para no bloquear la exploración."""
    from valeterna.ui.menus import _get_enemy_instance

    zone = ZONES[player.mundo["zona_actual"]]
    candidates = [e for e in zone.enemies if e in unlocked_enemies] or list(unlocked_enemies)
    if not candidates:
        console.info("No hay nada que explorar todavía.")
        return

    roll = random.random()
    if roll < _EXPLORE_ENCOUNTER_CHANCE:
        enemy_name = random.choice(candidates)
        # enemy_factory permite encadenar peleas si el jugador activa la
        # auto-batalla contra un enemigo ya derrotado (ver initiate_battle).
        initiate_battle(
            player,
            _get_enemy_instance(enemy_name),
            defeated_enemies,
            unlocked_enemies,
            enemy_factory=lambda: _get_enemy_instance(enemy_name),
        )
    elif roll < _EXPLORE_ENCOUNTER_CHANCE + _EXPLORE_DISCOVERY_CHANCE:
        _discovery(player)
    else:
        console.say("Exploras la zona, pero no encuentras nada de interés.")


def _discovery(player) -> None:
    """Hallazgo de "Explorar" (GDD §8.1): normalmente oro, a veces una poción
    de salud gratis — un poco de variedad en vez de ser siempre lo mismo."""
    from valeterna.items.potions.healing_potion import HealingPotion

    if random.random() < _DISCOVERY_POTION_CHANCE:
        console.success("🧪 Encuentras un pequeño alijo escondido en el camino.")
        player.inventory.add_item(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20))
    else:
        gold = random.randint(3, 10)
        player.inventory.gold += gold
        console.success(f"💰 Encuentras {gold} de oro en el camino.")


def _open_shop(player) -> None:
    from valeterna.shop.shop import Shop

    Shop().open(player)


def _open_forge(player) -> None:
    from valeterna.crafting.forge import Forge

    Forge().open(player)


def _rest_flow(player) -> None:
    """Posada (GDD §7.4): cura del todo y limpia los estados alterados a
    cambio de oro. Coste provisional, ver `_REST_COST_PER_LEVEL`."""
    print(console.colorize("\n--- POSADA ---", console.Fore.CYAN))
    if player.stats.health >= player.stats.max_health and not player.status_effects:
        console.info("Ya estás a plena forma; no necesitas descansar.")
        return

    cost = _REST_COST_PER_LEVEL * player.level
    print(f"Descansar cuesta {cost} de oro (tienes {player.inventory.gold}) y cura toda tu vida y estados.")
    if console.ask("¿Descansar? (s/n): ").strip().lower() != "s":
        return
    if player.inventory.gold < cost:
        console.error("No tienes oro suficiente para descansar.")
        return

    player.inventory.gold -= cost
    player.stats.health = player.stats.max_health
    player.status_effects.clear()
    console.success("Descansas en la posada. Recuperas toda tu vida y tus estados desaparecen.")


# Sub-lugares con un servicio de verdad detrás (v0.12.0-c) en vez de solo
# ambientación — de momento solo en Piedrablanca (GDD §3: "Shop / forge / rest
# live in Piedrablanca's sub-locations"). El resto de sub-lugares de
# Piedrablanca (p. ej. Refugio) y todos los de las demás zonas siguen siendo
# stubs hasta que existan NPCs/servicios propios (GDD §8.2/§8.3, v0.13.0).
_ZONE_SERVICES = {
    ("piedrablanca", "Mercado"): _open_shop,
    ("piedrablanca", "Herrería"): _open_forge,
    ("piedrablanca", "Taberna"): _rest_flow,
}


def _sublocation_flow(player, zone) -> None:
    """Lista los sub-lugares de la zona. Los que tienen un servicio de verdad
    (`_ZONE_SERVICES`) lo abren; el resto sigue siendo solo ambientación."""
    if not zone.sub_locations:
        console.info("No hay ningún sub-lugar que visitar aquí todavía.")
        return

    print(console.colorize(f"\n--- {zone.name.upper()} ---", console.Fore.CYAN))
    for i, place in enumerate(zone.sub_locations, 1):
        print(f"{i}. {place}")
    print(f"{len(zone.sub_locations) + 1}. Volver")

    choice = console.ask(f"\nElige un lugar (1-{len(zone.sub_locations) + 1}): ")
    if not choice.isdigit():
        console.error("Opción no válida.")
        return
    idx = int(choice) - 1
    if idx == len(zone.sub_locations):
        return
    if not (0 <= idx < len(zone.sub_locations)):
        console.error("Opción fuera de rango.")
        return

    place = zone.sub_locations[idx]
    service = _ZONE_SERVICES.get((zone.id, place))
    if service:
        service(player)
        return
    console.say(f"Recorres {place}, pero todavía no hay nada que hacer aquí.")


def _travel_flow(player, unlocked_enemies: list) -> None:
    """Fast-travel a cualquier zona ya visitada, más "viajar a la frontera"
    (la siguiente zona de la cadena) en cuanto sea alcanzable."""
    mundo = player.mundo
    current = mundo["zona_actual"]
    visited = list(mundo["zonas_visitadas"])

    options = [(ZONES[zid].name, zid) for zid in visited if zid != current]

    frontier = next_zone(current)
    if frontier and frontier not in visited and is_zone_reachable(frontier, unlocked_enemies):
        options.append((f"{ZONES[frontier].name} (frontera)", frontier))

    if not options:
        console.info("No hay ningún sitio al que viajar todavía.")
        return

    print(console.colorize("\n--- VIAJAR ---", console.Fore.CYAN))
    for i, (label, _) in enumerate(options, 1):
        print(f"{i}. {label}")
    print(f"{len(options) + 1}. Cancelar")

    choice = console.ask(f"\nElige destino (1-{len(options) + 1}): ")
    if not choice.isdigit():
        console.error("Opción no válida.")
        return
    idx = int(choice) - 1
    if idx == len(options):
        return
    if not (0 <= idx < len(options)):
        console.error("Opción fuera de rango.")
        return

    destination = options[idx][1]
    mundo["zona_actual"] = destination
    if destination not in mundo["zonas_visitadas"]:
        mundo["zonas_visitadas"].append(destination)
    console.success(f"Viajas a {ZONES[destination].name}.")


def _character_menu(player, unlocked_enemies: list, defeated_enemies: list, is_admin: bool) -> str | None:
    """Menú "Personaje" (GDD §8.1): todo lo que antes colgaba de `game_loop`
    salvo "Luchar" (ahora "Explorar") y Tienda/Herrería (ahora en "Ir a..." de
    Piedrablanca, v0.12.0-c). Devuelve `"volver_menu"` si el jugador elige
    volver al Menú Principal, o `None` si vuelve a la zona."""
    from valeterna.items.equipment import Weapon
    from valeterna.persistence.save_load import save_game
    from valeterna.ui.menus import _admin_panel_flow, _bestiary_flow, _equip_armor_flow, _skills_flow, open_options

    while True:
        print(console.colorize("\n--- PERSONAJE ---", console.Fore.MAGENTA, bright=True))

        options = [
            ("Inventario", lambda: player.inventory.show_inventory(mode="use")),
            ("Estadísticas", player.show_stats),
            ("Habilidades", lambda: _skills_flow(player)),
            ("Bestiario", lambda: _bestiary_flow(player, defeated_enemies)),
            ("Equipar Arma", lambda: player.inventory.equip_menu(Weapon)),
            ("Equipar Armadura", lambda: _equip_armor_flow(player)),
            ("Opciones", open_options),
            ("Guardar Partida", lambda: save_game(player, unlocked_enemies, defeated_enemies)),
            ("Volver a la zona", "volver_zona"),
            ("Volver al Menú Principal", "volver_menu"),
            ("Salir del Juego", sys.exit),
        ]
        if is_admin:
            options.insert(
                -2, ("Panel de Admin", lambda: _admin_panel_flow(player, unlocked_enemies, defeated_enemies))
            )

        for i, (label, _) in enumerate(options, 1):
            print(f"{i}. {label}")

        choice = console.ask(f"\nElige (1-{len(options)}): ")
        if not choice.isdigit():
            console.error("Opción no válida.")
            continue
        idx = int(choice) - 1
        if not (0 <= idx < len(options)):
            console.error("Opción fuera de rango.")
            continue

        label, action = options[idx]
        if action == "volver_zona":
            return None
        if action == "volver_menu":
            return "volver_menu"

        action()
        # Inventario/Estadísticas no tienen su propio "Presiona Enter..." (a
        # diferencia de Habilidades/Bestiario/Equipar, que ya paran solas en
        # su propio submenú), así que hace falta uno aquí para poder leerlas
        # antes de que el menú se vuelva a dibujar encima.
        if label in ("Inventario", "Estadísticas"):
            console.ask("\nPresiona Enter para continuar...")
