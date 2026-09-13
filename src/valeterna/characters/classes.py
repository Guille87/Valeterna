"""Clases de personaje (GDD §6.1 / §6.2.1).

Se elige una vez al crear el personaje y se guarda. Las partidas viejas y
cualquier `Player` construido sin especificar clase usan **Vagabundo**, que es
exactamente el personaje de siempre (todos los deltas a cero / multiplicadores a
uno).

Los números son **provisionales**: se recalibran en la fase de presupuesto de
poder (v0.14), ver `TODO.md`.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from valeterna.characters.stats import Stats

# Base de arranque del Vagabundo (la de `ui/menus.py::start_new_game` de siempre).
_BASE_HEALTH = 100
_BASE_MIN_ATK = 5
_BASE_MAX_ATK = 10
_BASE_ARMOR = 2
_BASE_CRIT_CHANCE = 0.15
_BASE_SPEED = 10
_BASE_EVASION = 0


class CharClass(str, Enum):
    VAGABUNDO = "vagabundo"
    GUERRERO = "guerrero"
    PICARO = "picaro"
    ARCANISTA = "arcanista"


@dataclass(frozen=True)
class ClassProfile:
    """Todo lo que una clase cambia respecto al Vagabundo."""

    id: CharClass
    name: str
    identity: str

    # Deltas sobre los stats de arranque.
    health_mult: float = 1.0
    atk_delta: int = 0
    armor_delta: int = 0
    speed_delta: int = 0
    evasion_delta: int = 0
    crit_chance_delta: float = 0.0
    magic_power: int = 0

    # Multiplicadores sobre las tasas de crecimiento por nivel de `Player`.
    armor_growth_mult: float = 1.0
    speed_growth_mult: float = 1.0
    # Tasa de crecimiento de `poder_magico` (0 = no crece).
    magic_power_growth_rate: float = 0.0

    # El ataque estándar es mágico (`is_magical`, escala con `poder_magico`).
    is_magical_attacker: bool = False


PROFILES: dict[CharClass, ClassProfile] = {
    # El valor guardado sigue siendo "vagabundo" (compatibilidad); solo cambia el
    # nombre visible.
    CharClass.VAGABUNDO: ClassProfile(
        id=CharClass.VAGABUNDO,
        name="Aventurero",
        identity="Equilibrado, sin fuertes ni débiles marcados. Buen punto de partida y el pool de habilidades más flexible.",
    ),
    CharClass.GUERRERO: ClassProfile(
        id=CharClass.GUERRERO,
        name="Guerrero",
        identity="Tanque / bruto. Más vida, armadura y daño físico; crece más resistente. Sin magia.",
        health_mult=1.15,
        atk_delta=1,
        armor_delta=2,
        armor_growth_mult=1.3,
    ),
    CharClass.PICARO: ClassProfile(
        id=CharClass.PICARO,
        name="Pícaro",
        identity="Ágil / crítico / veneno. Más velocidad, evasión y crítico; frágil.",
        health_mult=0.9,
        speed_delta=3,
        evasion_delta=5,
        crit_chance_delta=0.05,
        speed_growth_mult=1.3,
    ),
    CharClass.ARCANISTA: ClassProfile(
        id=CharClass.ARCANISTA,
        name="Arcanista",
        identity="Mágico / elemental. Menos vida y armadura; su ataque estándar es mágico y escala con poder mágico.",
        health_mult=0.85,
        armor_delta=-2,
        magic_power=8,
        magic_power_growth_rate=2.0,
        is_magical_attacker=True,
    ),
}

# Elemento por defecto del ataque básico del Arcanista cuando nada más lo fija
# (la pasiva "Sintonía" de M1 lo cambiará al empezar el combate, v0.10.0-c).
ARCANIST_DEFAULT_ELEMENT = "arcano"


def get_profile(char_class: CharClass | str | None) -> ClassProfile:
    """Perfil de una clase. Acepta el enum, su valor de texto o `None`
    (cualquier cosa desconocida cae en Vagabundo)."""
    if isinstance(char_class, CharClass):
        return PROFILES[char_class]
    try:
        return PROFILES[CharClass(char_class)]
    except ValueError:
        return PROFILES[CharClass.VAGABUNDO]


def starting_stats(char_class: CharClass | str | None) -> Stats:
    """Stats de arranque de un personaje nuevo de esa clase."""
    p = get_profile(char_class)
    health = round(_BASE_HEALTH * p.health_mult)
    return Stats(
        health,
        health,
        _BASE_MIN_ATK + p.atk_delta,
        _BASE_MAX_ATK + p.atk_delta,
        _BASE_ARMOR + p.armor_delta,
        crit_chance=_BASE_CRIT_CHANCE + p.crit_chance_delta,
        speed=_BASE_SPEED + p.speed_delta,
        evasion=_BASE_EVASION + p.evasion_delta,
        magic_power=p.magic_power,
    )
