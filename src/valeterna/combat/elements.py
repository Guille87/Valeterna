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

# --- Reacciones elementales (v0.11.0-c) ---------------------------------------
# "Fusión": un golpe de rayo contra un objetivo congelado rompe el hielo al
# instante y hace daño extra, en vez del intento normal de paralizar.
SHATTER_ELEMENT = "rayo"
SHATTER_FROZEN_STATUS = "congelado"
SHATTER_DAMAGE_MULT = 1.5

# "Combustión": quemado + veneno (en cualquier orden) se funden en un único
# estado más dañino que cualquiera de los dos por separado, en vez de coexistir.
COMBUSTION_STATUS = "combustion"
_COMBUSTION_PAIR = frozenset({"quemado", "veneno"})
COMBUSTION_MERGE_NAMES = _COMBUSTION_PAIR | {COMBUSTION_STATUS}


def is_shatter_hit(element: str | None, status_names) -> bool:
    """`True` si un golpe de `element` provoca la reacción "fusión" (rayo
    contra un objetivo ya congelado)."""
    return element == SHATTER_ELEMENT and SHATTER_FROZEN_STATUS in status_names


def is_status_blocked_by_combustion(current_statuses, incoming: str) -> bool:
    """`True` si `incoming` (quemado/veneno) no debe aplicarse porque el
    objetivo ya está en combustión, que ya representa a los dos: mientras
    dure, un nuevo intento de quemarlo/envenenarlo no hace nada (ni refresca
    la duración, ni vuelve a fundirlos)."""
    return incoming in _COMBUSTION_PAIR and COMBUSTION_STATUS in current_statuses


def resolve_status_reaction(current_statuses, incoming: str) -> str | None:
    """Si aplicar el estado `incoming` reacciona con uno ya presente en
    `current_statuses` (quemado + veneno -> combustión), devuelve el nombre del
    estado fusionado resultante. `None` si no hay reacción. No dispara si la
    combustión ya está activa (usar `is_status_blocked_by_combustion` antes)."""
    if incoming not in _COMBUSTION_PAIR:
        return None
    other = next(iter(_COMBUSTION_PAIR - {incoming}))
    if other in current_statuses:
        return COMBUSTION_STATUS
    return None


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


# Género gramatical de cada elemento, para construir frases en español que
# concuerden ("la oscuridad", no "el oscuridad"). Todos son masculinos salvo
# "oscuridad"; si se añaden elementos nuevos que sean femeninos, listarlos aquí.
_FEMININE_ELEMENTS = frozenset({"oscuridad"})


def element_phrase(element: str, *, capitalize: bool = False) -> str:
    """'el fuego' / 'la oscuridad' (o 'El'/'La' con `capitalize=True`, para
    empezar una frase)."""
    article = "la" if element in _FEMININE_ELEMENTS else "el"
    if capitalize:
        article = article.capitalize()
    return f"{article} {element}"


def element_al(element: str) -> str:
    """'al fuego' / 'a la oscuridad' (contracción a+el, o 'a la' si el
    elemento es femenino)."""
    return f"a la {element}" if element in _FEMININE_ELEMENTS else f"al {element}"
