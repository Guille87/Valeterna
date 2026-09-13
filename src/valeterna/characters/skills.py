"""Habilidades de clase (GDD §6.2 / §6.2.1 / §9.3).

Cada clase tiene un pool de habilidades que se desbloquean a lo largo de la
progresión, por nivel (las tempranas) o al derrotar al guardián de una zona (las
tardías — v0.14+). Dos tipos:

- **Pasiva**: siempre activa una vez aprendida. Se consulta con
  `Player.has_passive(id)` en los puntos de cálculo relevantes.
- **Activa**: una acción en vez de atacar, con enfriamiento en turnos. El jugador
  equipa hasta `MAX_EQUIPPED_ACTIVES`; el enfriamiento vive solo en el combate.

v0.10.0-b trae el motor + el hito M1 (1 activa + 1 pasiva por clase). Los hitos
M2-M7 y sus efectos llegan en fases posteriores. **Todos los números son
provisionales** (se recalibran en v0.14, ver `TODO.md`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from valeterna.characters.classes import CharClass

MAX_EQUIPPED_ACTIVES = 4

# Nivel provisional al que se aprende cada hito. M1 al crear, M2 al nivel 4; el
# resto son marcadores hasta que la fase de presupuesto de poder (v0.14) fije la
# curva y ate las habilidades tardías a guardianes de zona.
MILESTONE_LEVEL: dict[int, int] = {1: 1, 2: 4, 3: 8, 4: 12, 5: 16, 6: 20, 7: 25}


class SkillKind(str, Enum):
    PASSIVE = "passive"
    ACTIVE = "active"


@dataclass(frozen=True)
class Skill:
    id: str
    name: str
    char_class: CharClass
    kind: SkillKind
    milestone: int
    description: str
    cooldown: int = 0  # turnos, solo activas
    params: dict = field(default_factory=dict)

    @property
    def unlock_level(self) -> int:
        return MILESTONE_LEVEL[self.milestone]

    @property
    def is_active(self) -> bool:
        return self.kind is SkillKind.ACTIVE


CATALOG: dict[str, Skill] = {}


def _add(skill: Skill) -> None:
    CATALOG[skill.id] = skill


# --- Hito 1 (Los Yermos) — se aprende al crear el personaje --------------------

_add(
    Skill(
        "golpe_firme",
        "Golpe Firme",
        CharClass.VAGABUNDO,
        SkillKind.ACTIVE,
        1,
        "Un golpe que no puede fallar y hace un 40% más de daño.",
        cooldown=3,
        params={"guaranteed_hit": True, "damage_mult": 1.4},
    )
)
_add(
    Skill(
        "segundo_aliento",
        "Segundo Aliento",
        CharClass.VAGABUNDO,
        SkillKind.PASSIVE,
        1,
        "Al derrotar a un enemigo recuperas el 12% de tu vida máxima.",
        params={"heal_on_kill_pct": 0.12},
    )
)
_add(
    Skill(
        "embate",
        "Embate",
        CharClass.GUERRERO,
        SkillKind.ACTIVE,
        1,
        "Un golpe fuerte (+50% daño) con un 40% de probabilidad de aturdir al enemigo 1 turno.",
        cooldown=3,
        params={"damage_mult": 1.5, "stun_chance": 0.4},
    )
)
_add(
    Skill(
        "piel_de_piedra",
        "Piel de Piedra",
        CharClass.GUERRERO,
        SkillKind.PASSIVE,
        1,
        "Recibes un 12% menos de daño físico.",
        params={"phys_dmg_taken_mult": 0.88},
    )
)
_add(
    Skill(
        "golpe_bajo",
        "Golpe Bajo",
        CharClass.PICARO,
        SkillKind.ACTIVE,
        1,
        "Golpe crítico garantizado que además provoca sangrado.",
        cooldown=3,
        params={"guaranteed_hit": True, "force_crit": True, "bleed_turns": 3},
    )
)
_add(
    Skill(
        "reflejos",
        "Reflejos",
        CharClass.PICARO,
        SkillKind.PASSIVE,
        1,
        "+8 de evasión de forma permanente.",
        params={"evasion": 8},
    )
)
_add(
    Skill(
        "proyectil_arcano",
        "Proyectil Arcano",
        CharClass.ARCANISTA,
        SkillKind.ACTIVE,
        1,
        "Un proyectil mágico que ignora por completo la resistencia mágica del enemigo.",
        cooldown=2,
        params={"guaranteed_hit": True, "magical": True, "pierce_magic_resist": True},
    )
)
_add(
    Skill(
        "sintonia",
        "Sintonía",
        CharClass.ARCANISTA,
        SkillKind.PASSIVE,
        1,
        "Al empezar cada combate eliges el elemento de tu ataque.",
        params={"choose_element": True},
    )
)

# --- Hito 2 (Bosque de los Susurros) — se aprende al nivel 4 (provisional) -----

_add(
    Skill(
        "aguante",
        "Aguante",
        CharClass.VAGABUNDO,
        SkillKind.PASSIVE,
        2,
        "Por debajo del 30% de vida obtienes +15% de armadura y de resistencia mágica.",
        params={"low_hp_defense_pct": 0.15},
    )
)
_add(
    Skill(
        "represalia",
        "Represalia",
        CharClass.GUERRERO,
        SkillKind.PASSIVE,
        2,
        "30% de probabilidad de contraatacar cuando recibes un golpe físico.",
        params={"counter_chance": 0.30},
    )
)
_add(
    Skill(
        "veneno_de_contacto",
        "Veneno de Contacto",
        CharClass.PICARO,
        SkillKind.PASSIVE,
        2,
        "20% de probabilidad de envenenar al enemigo cuando lo golpeas.",
        params={"on_hit_poison_chance": 0.20},
    )
)
_add(
    Skill(
        "escudo_de_mana",
        "Escudo de Maná",
        CharClass.ARCANISTA,
        SkillKind.ACTIVE,
        2,
        "Te rodeas de un escudo que absorbe por completo el próximo golpe.",
        cooldown=4,
        params={"utility": True, "shield_next_hit": True},
    )
)


def pool_for(char_class: CharClass) -> list[Skill]:
    """Todas las habilidades de una clase, sin importar el nivel."""
    return [s for s in CATALOG.values() if s.char_class == char_class]


def known_skills(char_class: CharClass, level: int) -> list[Skill]:
    """Las habilidades que un personaje de esa clase y nivel ya ha aprendido."""
    return [s for s in pool_for(char_class) if level >= s.unlock_level]
