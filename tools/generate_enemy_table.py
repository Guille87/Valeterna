"""Genera docs/design/enemigos.md (y sus .csv hermanos): una tabla de
referencia de los 61 enemigos (zona, tier, stats, afinidades, mecánica y
drops), derivada directamente del código real en vez de mantenida a mano.

    python tools/generate_enemy_table.py

No forma parte del juego (no se importa desde `valeterna`, no tiene tests
propios, no afecta a `pyproject.toml`/cobertura) — es una herramienta de
diseño, igual que `characters/power_budget.py`, pensada para apoyar la
revisión de nombres/habilidades/drops repetidos o mal ordenados entre zonas
(ver TODO.md, sección "Pendiente ... revisión general antes de seguir con el
ROADMAP"). Como es generada, nunca se desincroniza del código: si algo
cambia, basta con volver a ejecutar este script y commitear el resultado.

El `.md` es para leer/diffear en el repo (con la tabla de Drops ya dividida
en sub-tablas por tipo); los `.csv` son para quien quiera filtrar/ordenar
libremente en una hoja de cálculo, algo que Markdown no permite.
"""

import csv
import os
import re
from pathlib import Path

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from valeterna.characters.power_budget import power_score, target_score
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.ui.menus import ALL_ENEMY_NAMES, _get_enemy_instance
from valeterna.world.map import ZONE_ORDER, ZONES, zone_for_enemy

REPO = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO / "docs" / "design"
OUTPUT_MD = OUTPUT_DIR / "enemigos.md"
OUTPUT_STATS_CSV = OUTPUT_DIR / "enemigos_stats.csv"
OUTPUT_AFFINITY_CSV = OUTPUT_DIR / "enemigos_afinidades.csv"
OUTPUT_DROPS_CSV = OUTPUT_DIR / "enemigos_drops.csv"

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

# Orden y título de las sub-tablas de Drops en el .md; "categoria" es el
# valor que lleva cada fila (ver _drop_rows()).
_DROP_CATEGORIES = [
    ("arma", "Armas"),
    ("armadura", "Armaduras"),
    ("material", "Materiales"),
    ("pocion", "Pociones"),
    ("otro", "Otros"),
]


def _plain(text: str) -> str:
    """Quita los códigos de color ANSI de colorama para volcarlos en Markdown/CSV."""
    return _ANSI_RE.sub("", text)


def _md_escape(text: str) -> str:
    return text.replace("|", "\\|")


def _set_str(names) -> str:
    return ", ".join(sorted(names)) if names else "—"


def _zone_and_tier(name: str, zone_display_cache: dict, tier_cache: dict):
    zone_id = zone_for_enemy(name)
    if zone_id not in zone_display_cache:
        zone_display_cache[zone_id] = ZONES[zone_id].name if zone_id else "—"
    tier: int | str = "—"
    if zone_id is not None and name in ZONES[zone_id].enemies:
        tier = ZONES[zone_id].enemies.index(name) + 1
    tier_cache[name] = tier
    return zone_display_cache[zone_id], tier


def _stats_rows() -> list[dict]:
    zone_display_cache: dict[str | None, str] = {}
    tier_cache: dict[str, int | str] = {}
    rows = []
    for position, name in enumerate(ALL_ENEMY_NAMES, start=1):
        enemy = _get_enemy_instance(name)
        cls = type(enemy)
        stats = enemy.stats
        zone_display, tier = _zone_and_tier(name, zone_display_cache, tier_cache)
        score = power_score(stats)
        zone_id = zone_for_enemy(name)
        deviation_str = "—"
        if zone_id is not None and isinstance(tier, int):
            target = target_score(ZONE_ORDER.index(zone_id), tier)
            deviation_str = f"{(score - target) / target * 100:+.0f}%"
        rows.append(
            {
                "#": position,
                "Zona": zone_display,
                "Tier": tier,
                "Nombre": name,
                "Tipo": cls.ENCOUNTER_KIND,
                "Poder real": round(score),
                "Desv. objetivo": deviation_str,
                "HP": stats.max_health,
                "Ataque": f"{stats.min_atk}-{stats.max_atk}",
                "Vel": stats.speed,
                "Crít (%/dmg)": f"{stats.crit_chance * 100:.0f}%/{stats.crit_damage * 100:.0f}%",
                "Armadura": stats.armor,
                "Res.Mágica": stats.magic_resist,
                "Precisión": stats.precision,
                "Evasión": stats.evasion,
                "Pen.Fís": stats.armor_penetration,
                "Pen.Mág": stats.magic_penetration,
                "Regen": stats.regen,
                "Oro": f"{enemy.gold_min}-{enemy.gold_max}",
            }
        )
    return rows, zone_display_cache, tier_cache


def _affinity_rows(zone_display_cache: dict, tier_cache: dict) -> list[dict]:
    rows = []
    for position, name in enumerate(ALL_ENEMY_NAMES, start=1):
        enemy = _get_enemy_instance(name)
        cls = type(enemy)
        zone_id = zone_for_enemy(name)
        rows.append(
            {
                "#": position,
                "Zona": zone_display_cache[zone_id],
                "Tier": tier_cache[name],
                "Nombre": name,
                "Elementos infligidos": _set_str(cls.ELEMENTS_DEALT),
                "Debilidades": _set_str(cls.WEAKNESSES),
                "Resistencias": _set_str(cls.RESISTANCES),
                "Inmune (elemento)": _set_str(cls.IMMUNE_ELEMENTS),
                "Inmune (estado)": _set_str(cls.IMMUNE_STATUSES),
                "Estados que inflige": _set_str(cls.INFLICTS),
                "Mecánica": cls.SIGNATURE or "—",
            }
        )
    return rows


def _drop_rows(zone_display_cache: dict, tier_cache: dict) -> list[dict]:
    rows = []
    for position, name in enumerate(ALL_ENEMY_NAMES, start=1):
        enemy = _get_enemy_instance(name)
        zone_id = zone_for_enemy(name)
        for item, prob in enemy.drop_table():
            if isinstance(item, Armor):
                categoria, tipo, stats_info = "armadura", f"armadura · {item.slot}", _plain(item.get_stats_info())
            elif isinstance(item, Weapon):
                categoria, tipo, stats_info = "arma", "arma", _plain(item.get_stats_info())
            elif isinstance(item, Material):
                categoria, tipo, stats_info = "material", "material", item.description
            elif type(item).__name__.endswith("Potion"):
                categoria, tipo, stats_info = "pocion", "poción", item.description
            else:
                categoria, tipo, stats_info = "otro", item.__class__.__name__, getattr(item, "description", "")
            rows.append(
                {
                    "#": position,
                    "Zona": zone_display_cache[zone_id],
                    "Tier": tier_cache[name],
                    "Enemigo": name,
                    "Objeto": item.name,
                    "Tipo": tipo,
                    "Stats": stats_info,
                    "Probabilidad": f"{prob * 100:.0f}%",
                    "Categoría": categoria,
                }
            )
    return rows


def _md_table(rows: list[dict], columns: list[str]) -> list[str]:
    lines = [
        "| " + " | ".join(columns) + " |",
        "|" + "|".join("---" for _ in columns) + "|",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_md_escape(str(row[col])) for col in columns) + " |")
    return lines


def _write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def generate_markdown(stats_rows, affinity_rows, drop_rows) -> str:
    stats_cols = list(stats_rows[0].keys())
    affinity_cols = list(affinity_rows[0].keys())
    drop_cols = [c for c in drop_rows[0] if c != "Categoría"]

    lines = [
        "# Tabla de referencia de enemigos",
        "",
        "> **Generado automáticamente por `tools/generate_enemy_table.py`. No editar a mano** — "
        "vuelve a ejecutar el script tras cualquier cambio de stats/drops/afinidades y commitea el resultado.",
        "",
        "Pensada como apoyo para la revisión de nombres/habilidades repetidos, el poder del equipo "
        "dropeado y las inversiones de calidad entre tiers de una misma zona (ver `TODO.md`). Para "
        "filtrar u ordenar libremente por cualquier columna, usa los `.csv` hermanos "
        "(`enemigos_stats.csv`, `enemigos_afinidades.csv`, `enemigos_drops.csv`) en una hoja de cálculo "
        "— Markdown no permite filtros interactivos.",
        "",
        "## Estadísticas de combate",
        "",
        *_md_table(stats_rows, stats_cols),
        "",
        "## Afinidades y mecánicas",
        "",
        *_md_table(affinity_rows, affinity_cols),
        "",
        "## Drops",
    ]

    for categoria, titulo in _DROP_CATEGORIES:
        rows = [r for r in drop_rows if r["Categoría"] == categoria]
        if not rows:
            continue
        lines += ["", f"### {titulo}", ""]
        lines += _md_table(rows, drop_cols)

    lines.append("")
    return "\n".join(lines)


def main() -> None:
    stats_rows, zone_display_cache, tier_cache = _stats_rows()
    affinity_rows = _affinity_rows(zone_display_cache, tier_cache)
    drop_rows = _drop_rows(zone_display_cache, tier_cache)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.write_text(generate_markdown(stats_rows, affinity_rows, drop_rows), encoding="utf-8")
    _write_csv(OUTPUT_STATS_CSV, stats_rows, list(stats_rows[0].keys()))
    _write_csv(OUTPUT_AFFINITY_CSV, affinity_rows, list(affinity_rows[0].keys()))
    _write_csv(OUTPUT_DROPS_CSV, drop_rows, list(drop_rows[0].keys()))

    for path in (OUTPUT_MD, OUTPUT_STATS_CSV, OUTPUT_AFFINITY_CSV, OUTPUT_DROPS_CSV):
        print(f"Escrito {path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
