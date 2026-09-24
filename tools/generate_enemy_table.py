"""Genera docs/design/enemigos.md: una tabla de referencia de los 61 enemigos
(zona, tier, stats, afinidades, mecánica y drops), derivada directamente del
código real en vez de mantenida a mano.

    python tools/generate_enemy_table.py

No forma parte del juego (no se importa desde `valeterna`, no tiene tests
propios, no afecta a `pyproject.toml`/cobertura) — es una herramienta de
diseño, igual que `characters/power_budget.py`, pensada para apoyar la
revisión de nombres/habilidades/drops repetidos o mal ordenados entre zonas
(ver TODO.md, sección "Pendiente ... revisión general antes de seguir con el
ROADMAP"). Como es generada, nunca se desincroniza del código: si algo
cambia, basta con volver a ejecutar este script y commitear el resultado.
"""

import os
import re
from pathlib import Path

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from valeterna.characters.power_budget import power_score, target_score
from valeterna.items.equipment import Armor, Weapon
from valeterna.ui.menus import ALL_ENEMY_NAMES, _get_enemy_instance
from valeterna.world.map import ZONE_ORDER, ZONES, zone_for_enemy

REPO = Path(__file__).resolve().parents[1]
OUTPUT = REPO / "docs" / "design" / "enemigos.md"

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _plain(text: str) -> str:
    """Quita los códigos de color ANSI de colorama para volcarlos en Markdown."""
    return _ANSI_RE.sub("", text)


def _md_escape(text: str) -> str:
    return text.replace("|", "\\|")


def _set_str(names) -> str:
    return ", ".join(sorted(names)) if names else "—"


def _row(zone_display: str, tier, position: int, enemy) -> str:
    cls = type(enemy)
    stats = enemy.stats
    score = power_score(stats)
    zone_id = zone_for_enemy(enemy.name)
    deviation_str = "—"
    if zone_id is not None and isinstance(tier, int):
        zone_index = ZONE_ORDER.index(zone_id)
        target = target_score(zone_index, tier)
        deviation_str = f"{(score - target) / target * 100:+.0f}%"
    return (
        f"| {position} | {zone_display} | {tier} | {_md_escape(enemy.name)} | {cls.ENCOUNTER_KIND} "
        f"| {score:,.0f} | {deviation_str} | {stats.max_health} | {stats.min_atk}-{stats.max_atk} "
        f"| {stats.speed} | {stats.crit_chance * 100:.0f}%/{stats.crit_damage * 100:.0f}% "
        f"| {stats.armor} | {stats.magic_resist} | {stats.precision} | {stats.evasion} "
        f"| {stats.armor_penetration} | {stats.magic_penetration} | {stats.regen} "
        f"| {enemy.gold_min}-{enemy.gold_max} |"
    )


def _affinity_row(zone_display: str, tier, position: int, enemy) -> str:
    cls = type(enemy)
    return (
        f"| {position} | {zone_display} | {tier} | {_md_escape(enemy.name)} "
        f"| {_set_str(cls.ELEMENTS_DEALT)} | {_set_str(cls.WEAKNESSES)} | {_set_str(cls.RESISTANCES)} "
        f"| {_set_str(cls.IMMUNE_ELEMENTS)} | {_set_str(cls.IMMUNE_STATUSES)} | {_set_str(cls.INFLICTS)} "
        f"| {_md_escape(cls.SIGNATURE) or '—'} |"
    )


def _drop_rows(zone_display: str, tier, position: int, enemy) -> list[str]:
    rows = []
    for item, prob in enemy.drop_table():
        if isinstance(item, Armor):
            kind = f"armadura · {item.slot}"
            stats_info = _plain(item.get_stats_info())
        elif isinstance(item, Weapon):
            kind = "arma"
            stats_info = _plain(item.get_stats_info())
        else:
            kind = item.__class__.__name__
            stats_info = getattr(item, "description", "")
        rows.append(
            f"| {position} | {zone_display} | {tier} | {_md_escape(enemy.name)} | {_md_escape(item.name)} "
            f"| {kind} | {_md_escape(stats_info)} | {prob * 100:.0f}% |"
        )
    return rows


def generate() -> str:
    lines = [
        "# Tabla de referencia de enemigos",
        "",
        "> **Generado automáticamente por `tools/generate_enemy_table.py`. No editar a mano** — "
        "vuelve a ejecutar el script tras cualquier cambio de stats/drops/afinidades y commitea el resultado.",
        "",
        "Pensada como apoyo para la revisión de nombres/habilidades repetidos, el poder del equipo "
        "dropeado y las inversiones de calidad entre tiers de una misma zona (ver `TODO.md`).",
        "",
        "## Estadísticas de combate",
        "",
        "| # | Zona | Tier | Nombre | Tipo | Poder real | Desv. objetivo | HP | Ataque | Vel "
        "| Crít (%/dmg) | Armadura | Res.Mágica | Precisión | Evasión | Pen.Fís | Pen.Mág | Regen | Oro |",
        "|---|------|------|--------|------|-----------:|----------------:|---:|--------|----:"
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]

    zone_display_cache: dict[str | None, str] = {}
    tier_cache: dict[str, int | str] = {}

    for position, name in enumerate(ALL_ENEMY_NAMES, start=1):
        enemy = _get_enemy_instance(name)
        zone_id = zone_for_enemy(name)
        if zone_id not in zone_display_cache:
            zone_display_cache[zone_id] = ZONES[zone_id].name if zone_id else "—"
        zone_display = zone_display_cache[zone_id]
        tier: int | str = "—"
        if zone_id is not None:
            enemies = ZONES[zone_id].enemies
            if name in enemies:
                tier = enemies.index(name) + 1
        tier_cache[name] = tier
        lines.append(_row(zone_display, tier, position, enemy))

    lines += [
        "",
        "## Afinidades y mecánicas",
        "",
        "| # | Zona | Tier | Nombre | Elementos infligidos | Debilidades | Resistencias "
        "| Inmune (elemento) | Inmune (estado) | Estados que inflige | Mecánica (`SIGNATURE`) |",
        "|---|------|------|--------|----|----|----|----|----|----|----|",
    ]
    for position, name in enumerate(ALL_ENEMY_NAMES, start=1):
        enemy = _get_enemy_instance(name)
        zone_id = zone_for_enemy(name)
        zone_display = zone_display_cache[zone_id]
        lines.append(_affinity_row(zone_display, tier_cache[name], position, enemy))

    lines += [
        "",
        "## Drops",
        "",
        "| # | Zona | Tier | Enemigo | Objeto | Tipo | Stats | Probabilidad |",
        "|---|------|------|---------|--------|------|-------|--------------:|",
    ]
    for position, name in enumerate(ALL_ENEMY_NAMES, start=1):
        enemy = _get_enemy_instance(name)
        zone_id = zone_for_enemy(name)
        zone_display = zone_display_cache[zone_id]
        lines += _drop_rows(zone_display, tier_cache[name], position, enemy)

    lines.append("")
    return "\n".join(lines)


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(generate(), encoding="utf-8")
    print(f"Escrito {OUTPUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
