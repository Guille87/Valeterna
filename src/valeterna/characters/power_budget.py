"""Herramienta de presupuesto de poder (GDD §4.4, v0.14.0-b).

No es una pantalla del juego: es una herramienta de **diseño**, usada al escribir
el roster de una zona (v0.14.0-c/d en adelante) para saber si un enemigo nuevo
está sobre o infra-tuneado antes de escribir su código, en vez de descubrirlo a
mano con cientos de combates simulados.

**La fórmula (`power_score`)**: `vida_máxima × velocidad × daño_neto`, donde
`daño_neto` es el daño medio del enemigo ajustado por su propio crítico
(`daño_medio × (1 + crit_chance × (crit_damage - 1))`). Deliberadamente **no**
resta la mitigación de un jugador de referencia — no hay un jugador "típico"
fijo (varía por clase/nivel/equipo), así que restar algo aquí sería más
especulativo que no restar nada. La fórmula mide la amenaza *intrínseca* del
enemigo (vida + frecuencia de turno + daño); si encaja de verdad contra un
jugador real lo confirma el playtest posterior, tal como pide el GDD ("design
... then playtest-verify").

**Limitación conocida**: la fórmula solo ve `min_atk`/`max_atk` — no captura
mecánicas que añaden amenaza sin subir esas stats directamente (autocuración,
reanimación, robo de estados, control de daño en el tiempo). El Esqueleto
(revive una vez a mitad de vida) y el Mago (curación + control, con un ataque
base deliberadamente bajo) son los dos casos conocidos entre los 14 actuales —
ver el informe en `TODO.md`.

**La curva objetivo** `objetivo(zona, tier) = BASE · ZONE_GROWTH^zona ·
TIER_GROWTH^(tier-1)` — geométrica en ambos ejes, la forma natural de una curva
de poder de RPG. Las constantes se ajustaron por regresión log-lineal contra
datos reales: `ZONE_GROWTH` contra el poder medio de las 6 zonas ya pobladas
(`zone` = índice en `world.map.ZONE_ORDER`, Piedrablanca=0); `TIER_GROWTH`
contra la única zona con tiers ya fijados por el GDD (Los Yermos §4.6: Goblin=2,
Huargo=4, Esqueleto=6, Bandido=7 — el resto de zonas no tiene tiers de diseño
todavía, así que no se le asignan aquí; eso es trabajo de cada sub-fase que
rellene esa zona). Redondeadas a números limpios tras el ajuste: `BASE=1500`,
`ZONE_GROWTH=2.1` (el poder medio de una zona ronda el doble de la anterior),
`TIER_GROWTH=1.25` (cada tier dentro de una zona sube ~25% sobre el anterior).
"""

BASE = 1500.0
ZONE_GROWTH = 2.1
TIER_GROWTH = 1.25

# Tolerancia de diseño del GDD §4.4: "design each enemy within ±10% of its
# target". No fuerza nada por sí sola, la usan los callers que quieran avisar.
DESIGN_TOLERANCE = 0.10


def power_score(stats) -> float:
    """Amenaza intrínseca de un enemigo: `vida_máxima × velocidad × daño_neto`."""
    mean_damage = (stats.min_atk + stats.max_atk) / 2
    crit_factor = 1 + stats.crit_chance * (stats.crit_damage - 1)
    net_damage = mean_damage * crit_factor
    return stats.max_health * stats.speed * net_damage


def target_score(zone_index: int, tier: int) -> float:
    """Objetivo de poder para el tier `tier` (1-10) de la zona en la posición
    `zone_index` de `world.map.ZONE_ORDER`."""
    return BASE * ZONE_GROWTH**zone_index * TIER_GROWTH ** (tier - 1)


def zone_score_range(zone_index: int) -> tuple[float, float]:
    """`(objetivo(zona, tier=1), objetivo(zona, tier=10))` — el rango de poder
    válido para *cualquier* enemigo de esa zona, sin necesidad de saber su tier
    exacto (útil para las zonas cuyos tiers no están fijados todavía)."""
    return target_score(zone_index, 1), target_score(zone_index, 10)


def deviation(actual: float, target: float) -> float:
    """Desviación de `actual` sobre `target`, como fracción (`0.15` = +15%)."""
    return (actual - target) / target
