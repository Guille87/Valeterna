"""Mide el poder efectivo del jugador contra el `power_score()` real de los
enemigos, simulando un **grindeo realista** en vez de "un combate por
enemigo": el patrón exacto que dio el usuario tras jugar de verdad — 20
combates seguidos contra cada enemigo (1 manual + 19 en Auto-Batalla Turbo)
antes de pasar al siguiente tier — en vez de la primera versión de esta
herramienta, que solo contaba el mínimo para desbloquear toda la cadena y se
quedó muy corta al validarla contra una partida real.

    python tools/measure_player_power.py [--kills-per-enemy 20] [--zone ZONE_ID]
    python tools/measure_player_power.py --growth-scale 0.4   # prueba un
        recorte del ritmo de subida de stats por nivel sin tocar player.py

Por defecto simula las 7 zonas pobladas, 20 combates por enemigo. No forma
parte del juego — herramienta de diseño, igual que `characters/power_budget.py`
y `tools/generate_enemy_table.py`.
"""

import argparse
import builtins
import os
import random

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from valeterna.characters.classes import CharClass, starting_stats
from valeterna.characters.player import Player
from valeterna.characters.power_budget import power_score
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


def power_no_gear(player: Player) -> float:
    s = player.stats
    mean_damage = (s.min_atk + s.max_atk) / 2
    crit_factor = 1 + s.crit_chance * (s.crit_damage - 1)
    return s.max_health * s.speed * mean_damage * crit_factor


def power_with_gear(player: Player) -> float:
    lo, hi = player.get_attack_range()
    mean_damage = (lo + hi) / 2
    crit_factor = 1 + player.get_total_crit_chance() * (player.get_total_crit_damage() - 1)
    return player.stats.max_health * player.get_total_speed() * mean_damage * crit_factor


def _armor_score(item: Armor) -> float:
    return getattr(item, _BASE_STAT_BY_SLOT[item.slot])


def _fight(player: Player, enemy_name: str, weapon_dmg: dict, ring_state: list) -> None:
    """Una "pelea" simplificada: solo XP/oro (con la misma penalización por
    sobre-nivel que el juego real, ver `combat.battle._xp_multiplier_for_overlevel`)
    y equipar lo mejor disponible de los drops del enemigo (optimista: asume
    que tarde o temprano caen todos). No simula el combate turno a turno —
    para eso ya está `initiate_battle()` / `tools/measure_combat_turns.py`."""
    from valeterna.combat.battle import _xp_multiplier_for_overlevel

    enemy = _get_enemy_instance(enemy_name)
    gold = (enemy.gold_min + enemy.gold_max) / 2
    xp_mult = _xp_multiplier_for_overlevel(player.level, enemy_name)
    player.gain_experience(round(gold * 2 * xp_mult))

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


_GROWTH_ATTRS = (
    "_HEALTH_GROWTH_RATE",
    "_MIN_ATK_GROWTH_RATE",
    "_MAX_ATK_GROWTH_RATE",
    "_ARMOR_GROWTH_RATE",
    "_SPEED_GROWTH_RATE",
)


def simulate(
    kills_per_enemy: int = 20,
    zone_ids: list[str] | None = None,
    seed: int = 0,
    growth_scale: float = 1.0,
) -> list[dict]:
    """Simula limpiar cada zona (por defecto las 7 pobladas, en orden) matando
    cada enemigo `kills_per_enemy` veces seguidas antes de pasar al
    siguiente — el patrón real que dio el usuario: 1 combate manual para
    desbloquear + 19 en Auto-Batalla Turbo contra ESE MISMO enemigo antes de
    avanzar al siguiente tier (200 combates totales en una zona de 10, no
    repartidos al azar por la zona como en la primera versión de esta
    herramienta, que se quedó muy corta). Devuelve una fila por tier con el
    nivel y el poder del jugador alcanzados justo al terminar de "agotar" ese
    tier, y el `power_score()` real de ese tier."""
    random.seed(seed)
    builtins.print = _silent
    originals = {attr: getattr(Player, attr) for attr in _GROWTH_ATTRS}
    for attr in _GROWTH_ATTRS:
        setattr(Player, attr, originals[attr] * growth_scale)
    try:
        player = Player("Sim", starting_stats(CharClass.VAGABUNDO), char_class=CharClass.VAGABUNDO)
        weapon_dmg = {"dmg": 0}
        ring_state: list = []
        rows = []

        for zone_id in ZONE_ORDER:
            zone = ZONES[zone_id]
            if not zone.enemies or (zone_ids and zone_id not in zone_ids):
                continue

            for tier, name in enumerate(zone.enemies, start=1):
                for _ in range(kills_per_enemy):
                    _fight(player, name, weapon_dmg, ring_state)

                enemy = _get_enemy_instance(name)
                rows.append(
                    {
                        "zone": zone.name,
                        "tier": tier,
                        "enemy": name,
                        "level": player.level,
                        "experience": player.experience,
                        "enemy_power": power_score(enemy.stats),
                        "player_power": power_with_gear(player),
                    }
                )
        return rows
    finally:
        builtins.print = _print
        for attr, value in originals.items():
            setattr(Player, attr, value)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--kills-per-enemy",
        type=int,
        default=20,
        help="Combates seguidos contra cada enemigo antes de pasar al siguiente tier (por defecto 20).",
    )
    parser.add_argument(
        "--zone", action="append", dest="zones", help="Limita a esta zona (repetible). Por defecto, todas."
    )
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--growth-scale",
        type=float,
        default=1.0,
        help="Escala temporal (solo para esta simulación) del ritmo de subida de stats por nivel del jugador.",
    )
    args = parser.parse_args()

    rows = simulate(
        kills_per_enemy=args.kills_per_enemy, zone_ids=args.zones, seed=args.seed, growth_scale=args.growth_scale
    )

    print(f"Grindeo simulado: {args.kills_per_enemy} combates seguidos contra cada enemigo antes de avanzar\n")
    print(
        f"{'Zona':28s} {'Tier':>4s} {'Enemigo':32s} {'Nivel':>5s} {'XP':>8s} "
        f"{'PoderEnem':>12s} {'PoderPJ':>12s} {'Ratio':>8s}"
    )
    for r in rows:
        ratio = r["player_power"] / r["enemy_power"] if r["enemy_power"] else float("inf")
        print(
            f"{r['zone']:28s} {r['tier']:>4d} {r['enemy']:32s} {r['level']:>5d} {r['experience']:>8,d} "
            f"{r['enemy_power']:>12,.0f} {r['player_power']:>12,.0f} {ratio:>7.2f}x"
        )


if __name__ == "__main__":
    main()
