"""Mide la dificultad real de un combate en **turnos**, no en un ratio de
poder abstracto: cuántos turnos le hace falta al jugador para matar a cada
enemigo, y cuántos le haría falta al enemigo para matar al jugador, en el
momento exacto en que se lo encontraría jugando con normalidad (nivel +
equipo acumulados hasta ese punto de la cadena, un combate por enemigo).

Usa las mismas fórmulas del motor de combate real (`resolve_hit()`,
`apply_mitigation()`) pero en valor esperado en vez de tirar dados, así el
resultado es determinista y rápido de iterar. Ignora mecánicas especiales de
cada enemigo (autocuración, golpes extra, estados) — es una primera pasada
para calibrar vida/ataque base, no una simulación completa turno a turno.

    python tools/measure_combat_turns.py --zone los_yermos
    python tools/measure_combat_turns.py --zone los_yermos --enemy-hp-scale 3.0 --enemy-atk-scale 1.5

No forma parte del juego — herramienta de diseño, igual que
`characters/power_budget.py` y `tools/measure_player_power.py` (de donde
reutiliza el bucle de progresión nivel + equipo).
"""

import argparse
import builtins
import os

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from valeterna.characters.classes import CharClass, starting_stats
from valeterna.characters.player import Player
from valeterna.characters.stats import DEFENSE_SOFTENING
from valeterna.items.equipment import Armor, Weapon
from valeterna.ui.menus import _get_enemy_instance
from valeterna.world.map import ZONE_ORDER, ZONES

_print = builtins.print


def _silent(*_a, **_k) -> None:
    pass


_BASE_STAT_BY_SLOT = {
    "casco": "max_health",
    "peto": "defense",
    "hombreras": "precision",
    "brazales": "crit_chance",
    "guantes": "crit_damage",
    "cinturon": "defense",
    "perneras": "evasion",
    "botas": "speed",
    "anillo": "crit_damage",
    "amuleto": "magic_resist",
}


def _armor_score(item: Armor) -> float:
    return getattr(item, _BASE_STAT_BY_SLOT[item.slot])


def _hit_chance(attacker_precision: float, defender_evasion: float) -> float:
    return max(5.0, min(100.0, 100.0 + attacker_precision - defender_evasion)) / 100.0


def _expected_damage(mean_atk: float, mitigation: float, crit_chance: float, crit_damage: float) -> float:
    mitigation = max(0.0, mitigation)
    mitigated = mean_atk * DEFENSE_SOFTENING / (mitigation + DEFENSE_SOFTENING)
    crit_factor = 1 + crit_chance * (crit_damage - 1)
    return mitigated * crit_factor


def turns_to_kill_enemy(player: Player, enemy) -> float:
    lo, hi = player.get_attack_range()
    mean_atk = (lo + hi) / 2
    dmg = _expected_damage(mean_atk, enemy.stats.armor, player.get_total_crit_chance(), player.get_total_crit_damage())
    hit = _hit_chance(player.get_total_precision(), enemy.stats.evasion)
    dmg_per_turn = dmg * hit
    return enemy.stats.max_health / dmg_per_turn if dmg_per_turn > 0 else float("inf")


def turns_to_kill_player(player: Player, enemy) -> float:
    mean_atk = (enemy.stats.min_atk + enemy.stats.max_atk) / 2
    dmg = _expected_damage(mean_atk, player.get_total_armor(), enemy.stats.crit_chance, enemy.stats.crit_damage)
    hit = _hit_chance(enemy.stats.precision, player.get_total_evasion())
    dmg_per_turn = dmg * hit
    return player.stats.max_health / dmg_per_turn if dmg_per_turn > 0 else float("inf")


def _fight_and_equip(player: Player, enemy_name: str, weapon_dmg: dict, ring_state: list) -> None:
    enemy = _get_enemy_instance(enemy_name)
    gold = (enemy.gold_min + enemy.gold_max) / 2
    player.gain_experience(round(gold * 2))
    for item, _prob in enemy.drop_table():
        if isinstance(item, Weapon):
            if item.damage > weapon_dmg["dmg"]:
                weapon_dmg["dmg"] = item.damage
                player.equipped_weapon = item
        elif isinstance(item, Armor):
            if item.slot == "anillo":
                ring_state.append(item)
                ring_state.sort(key=lambda a: a.crit_damage, reverse=True)
                del ring_state[2:]
                player.equipped_armor["anillo1"] = ring_state[0] if len(ring_state) > 0 else None
                player.equipped_armor["anillo2"] = ring_state[1] if len(ring_state) > 1 else None
            else:
                current = player.equipped_armor.get(item.slot)
                if current is None or _armor_score(item) >= _armor_score(current):
                    item.use(player, target_slot=item.slot)


def simulate(
    zone_ids: list[str] | None = None,
    enemy_hp_scale: tuple[float, float] = (1.0, 1.0),
    enemy_atk_scale: tuple[float, float] = (1.0, 1.0),
) -> list[dict]:
    """Progresión de "un combate por enemigo" (nivel + equipo acumulados con
    normalidad), midiendo los turnos esperados justo antes de cada combate —
    la dificultad tal como la sentiría el jugador la primera vez que se
    encuentra a ese enemigo. `enemy_hp_scale`/`enemy_atk_scale` son
    `(tier1, tier10)`: el multiplicador temporal (sin tocar los archivos de
    enemigo) se interpola linealmente entre el primer y el último tier de
    cada zona, para no castigar el primer combate igual que el último."""
    builtins.print = _silent
    try:
        player = Player("Sim", starting_stats(CharClass.VAGABUNDO), char_class=CharClass.VAGABUNDO)
        weapon_dmg = {"dmg": 0}
        ring_state: list = []
        rows = []

        for zone_id in ZONE_ORDER:
            zone = ZONES[zone_id]
            if not zone.enemies or (zone_ids and zone_id not in zone_ids):
                continue

            n = len(zone.enemies)
            for tier, name in enumerate(zone.enemies, start=1):
                frac = (tier - 1) / (n - 1) if n > 1 else 0.0
                hp_scale = enemy_hp_scale[0] + (enemy_hp_scale[1] - enemy_hp_scale[0]) * frac
                atk_scale = enemy_atk_scale[0] + (enemy_atk_scale[1] - enemy_atk_scale[0]) * frac

                enemy = _get_enemy_instance(name)
                enemy.stats.max_health = round(enemy.stats.max_health * hp_scale)
                enemy.stats.health = enemy.stats.max_health
                enemy.stats.min_atk = round(enemy.stats.min_atk * atk_scale)
                enemy.stats.max_atk = round(enemy.stats.max_atk * atk_scale)

                rows.append(
                    {
                        "zone": zone.name,
                        "tier": tier,
                        "enemy": name,
                        "level": player.level,
                        "turns_to_kill_enemy": turns_to_kill_enemy(player, enemy),
                        "turns_to_kill_player": turns_to_kill_player(player, enemy),
                    }
                )
                _fight_and_equip(player, name, weapon_dmg, ring_state)
        return rows
    finally:
        builtins.print = _print


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--zone", action="append", dest="zones", help="Limita a esta zona (repetible). Por defecto, todas."
    )
    parser.add_argument("--enemy-hp-scale", type=float, nargs=2, default=[1.0, 1.0], metavar=("TIER1", "TIER10"))
    parser.add_argument("--enemy-atk-scale", type=float, nargs=2, default=[1.0, 1.0], metavar=("TIER1", "TIER10"))
    args = parser.parse_args()

    rows = simulate(
        zone_ids=args.zones,
        enemy_hp_scale=tuple(args.enemy_hp_scale),
        enemy_atk_scale=tuple(args.enemy_atk_scale),
    )

    print(
        f"Escala probada: vida x{args.enemy_hp_scale[0]}->x{args.enemy_hp_scale[1]}, ataque x{args.enemy_atk_scale[0]}->x{args.enemy_atk_scale[1]}\n"
    )
    print(f"{'Zona':28s} {'Tier':>4s} {'Enemigo':32s} {'Nivel':>5s} {'Turnos mata PJ':>15s} {'Turnos muere PJ':>16s}")
    for r in rows:
        print(
            f"{r['zone']:28s} {r['tier']:>4d} {r['enemy']:32s} {r['level']:>5d} "
            f"{r['turns_to_kill_enemy']:>14.1f}  {r['turns_to_kill_player']:>15.1f}"
        )


if __name__ == "__main__":
    main()
