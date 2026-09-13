"""Elementos de daño y su modelo de afinidad (GDD §5).

Cada fuente de daño lleva como mucho un elemento: el arma equipada, una
habilidad, un ataque de enemigo, o `None` = daño físico puro. Cuatro elementos
golpean como daño físico (se mitigan con armadura) y tres como daño mágico (se
mitigan con resistencia mágica).

Cada tipo de enemigo declara sus afinidades como conjuntos de clase
(`WEAKNESSES` / `RESISTANCES` / `IMMUNE_ELEMENTS` / `IMMUNE_STATUSES`);
`affinity_multiplier()` los combina en un único multiplicador de daño:

- **Inmune**: el elemento hace ×0 (y su estado nunca se aplica).
- **Débil**: ×1.5; ×2.0 si el ataque combina dos elementos de debilidad.
- **Resistente**: ×0.5; ×0.25 si combina dos de resistencia. La resistencia
  además reduce a la mitad la probabilidad y duración del estado (eso lo aplica
  quien procesa `apply_status`, no esta función).
"""

PHYSICAL_ELEMENTS = frozenset({"fuego", "veneno", "rayo", "hielo"})
MAGICAL_ELEMENTS = frozenset({"sagrado", "oscuridad", "arcano"})
ELEMENTS = PHYSICAL_ELEMENTS | MAGICAL_ELEMENTS

# Estado que aplica cada elemento al golpear (arma con `inflicts`, habilidad...).
ELEMENT_STATUS = {
    "fuego": "quemado",
    "veneno": "veneno",
    "rayo": "paralizado",
    "hielo": "congelado",
    "sagrado": "consagrado",
    "oscuridad": "marchito",
    "arcano": "fractura_magica",
}

_WEAK_SINGLE = 1.5
_WEAK_DOUBLE = 2.0
_RESIST_SINGLE = 0.5
_RESIST_DOUBLE = 0.25


def is_magical_element(element: str | None) -> bool:
    """`True` si el elemento se mitiga con resistencia mágica (sagrado/oscuridad/arcano)."""
    return element in MAGICAL_ELEMENTS


def affinity_multiplier(elements, *, weaknesses, resistances, immune_elements) -> float:
    """Multiplicador de daño para un ataque de `elements` (normalmente un solo
    elemento; dos si es un golpe o reacción de doble elemento) contra un objetivo
    con esas afinidades. `elements` puede traer `None`, que se ignora."""
    elements = {e for e in elements if e}
    if not elements:
        return 1.0
    if elements & set(immune_elements):
        return 0.0

    multiplier = 1.0

    weak_hits = len(elements & set(weaknesses))
    if weak_hits >= 2:
        multiplier *= _WEAK_DOUBLE
    elif weak_hits == 1:
        multiplier *= _WEAK_SINGLE

    resist_hits = len(elements & set(resistances))
    if resist_hits >= 2:
        multiplier *= _RESIST_DOUBLE
    elif resist_hits == 1:
        multiplier *= _RESIST_SINGLE

    return multiplier
