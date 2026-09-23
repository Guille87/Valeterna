"""Herramienta de presupuesto de poder (GDD §4.4, v0.14.0-b): la fórmula de
amenaza, la curva objetivo, y un informe de los 14 enemigos actuales contra
esa curva (no para "aprobarlos" — muchos se diseñaron antes de que existiera
esta herramienta — sino para dejar constancia de dónde caen y por qué)."""

from valeterna.characters.power_budget import (
    DESIGN_TOLERANCE,
    deviation,
    power_score,
    target_score,
    zone_score_range,
)
from valeterna.characters.stats import Stats
from valeterna.combat.battle import ENEMY_PROGRESSION
from valeterna.ui.menus import _get_enemy_instance
from valeterna.world.map import ZONE_ORDER, zone_for_enemy


def _stats(**kwargs):
    base = {
        "health": 100,
        "max_health": 100,
        "min_atk": 10,
        "max_atk": 20,
        "armor": 0,
        "speed": 10,
        "crit_chance": 0.0,
        "crit_damage": 1.5,
    }
    base.update(kwargs)
    return Stats(**base)


# --- power_score ----------------------------------------------------------------


def test_power_score_is_health_times_speed_times_mean_damage_without_crit():
    s = _stats(health=200, max_health=200, min_atk=10, max_atk=30, speed=5, crit_chance=0.0)
    assert power_score(s) == 200 * 5 * 20  # daño medio 20, sin crítico que lo ajuste


def test_power_score_grows_with_crit_chance_and_crit_damage():
    baseline = _stats(crit_chance=0.0)
    with_crit = _stats(crit_chance=0.5, crit_damage=2.0)
    assert power_score(with_crit) > power_score(baseline)


def test_power_score_is_zero_for_a_dead_weight_enemy_with_no_attack():
    s = _stats(min_atk=0, max_atk=0)
    assert power_score(s) == 0


# --- target_score / zone_score_range ---------------------------------------------


def test_target_score_increases_with_zone_and_with_tier():
    assert target_score(2, 5) > target_score(1, 5)  # más zona, más poder
    assert target_score(2, 5) > target_score(2, 1)  # más tier, más poder


def test_target_score_curve_is_strictly_increasing_within_a_zone_and_across_zones():
    # Dentro de una zona, cada tier supera al anterior.
    for zone in range(len(ZONE_ORDER)):
        tier_values = [target_score(zone, tier) for tier in range(1, 11)]
        assert tier_values == sorted(set(tier_values))
    # A igualdad de tier, cada zona supera a la anterior. (No se exige que el
    # tier 10 de una zona supere al tier 1 de la siguiente — un guardián puede
    # ser más duro que el trámite más flojo de la zona de después.)
    for tier in (1, 5, 10):
        zone_values = [target_score(zone, tier) for zone in range(len(ZONE_ORDER))]
        assert zone_values == sorted(set(zone_values))


def test_zone_score_range_bounds_match_tier_1_and_tier_10():
    lo, hi = zone_score_range(3)
    assert lo == target_score(3, 1)
    assert hi == target_score(3, 10)
    assert lo < hi


# --- deviation --------------------------------------------------------------------


def test_deviation_is_a_fraction_positive_above_and_negative_below_target():
    assert deviation(115, 100) == 0.15
    assert deviation(85, 100) == -0.15
    assert deviation(100, 100) == 0.0


# --- Informe sobre los 14 enemigos actuales ---------------------------------------

_ZONE_INDEX = {zone_id: i for i, zone_id in enumerate(ZONE_ORDER)}

# Único tramo con tiers fijados por el GDD (§4.6, tabla de Los Yermos). El
# resto de zonas no tiene tiers de diseño todavía (ver docstring del módulo).
_YERMOS_TIERS = {"Goblin": 2, "Huargo": 4, "Esqueleto": 6, "Bandido": 7}

# Enemigos cuyo poder cae fuera de [tier1, tier10] de su zona, ya calibrados
# por playtest antes de que existiera esta herramienta — no se retocan aquí
# (es un rebalanceo aparte, ver TODO.md), solo se documenta que se conoce y
# por qué: Espíritu Vengativo es más rápido y letal de lo que "toca" para ser
# de los primeros enemigos de su zona; el Gólem de Piedra es, con diferencia,
# el más resistente de todo el roster hasta ahora.
#
# Los 6 enemigos del Bosque de los Susurros de v0.14.0-e (tiers 4-10, todos
# menos Araña Tejesombras) también caen aquí, pero por un motivo distinto y
# deliberado: el rango [tier1, tier10] de una zona lo marca la curva
# *objetivo*, que reinicia baja en cada zona nueva — pero Troll (tier 3, ya
# implementado antes de esta herramienta) tiene un poder REAL de ~38.062,
# muy por encima de su propio objetivo (~10.336) y ya cerca del techo del
# rango de toda la zona (49.286). Diseñar los tiers 4-10 contra la curva
# objetivo en vez de contra el poder real de Troll habría significado que la
# dificultad *bajara* justo después de él — lo contrario de lo que pide el
# usuario ("si se llega al Bosque es porque se ha superado Los Yermos, así
# que el Bosque tiene que ser más difícil, y así sucesivamente"). En su
# lugar, cada tier nuevo se diseñó por encima del poder real del anterior
# (Troll → Araña → Druida → ... → El Enraizado), y El Enraizado (guardián,
# ~112.225) se dejó deliberadamente por debajo de Gárgola (primer enemigo del
# Cañón del Trueno, ~120.350) para que la transición de zona siga siendo
# progresiva. Ver TODO.md para la tabla completa de poder real por tier.
_KNOWN_OUT_OF_RANGE = {
    "Espíritu Vengativo",
    "Gólem de Piedra",
    "Druida Corrupto",
    "Oso Espectral",
    "Enjambre de Polillas Pálidas",
    "Lobo Umbrío",
    "Ent Corrompido",
    "El Enraizado",
    # Ciénaga de los Ahogados (v0.14.0-f): mismo motivo que los 6 de arriba
    # del Bosque — el rango formal de la zona resetea bajo en cada zona
    # nueva, pero El Enraizado (guardián del Bosque, ya implementado) tiene
    # un poder real (~112.225) muy por encima de su propio rango. Diseñar
    # los 10 tiers de la Ciénaga contra la curva formal en vez de contra el
    # poder real de El Enraizado los habría hecho más débiles que el
    # enemigo que el jugador acaba de superar — así que, igual que en el
    # Bosque, cada tier se dimensionó para superar el poder real del
    # anterior (~118.818 → ~205.746), y Gárgola (guardián que sigue a la
    # Ciénaga) se reforzó a su vez (~214.245) para que la transición de
    # zona también siga siendo progresiva.
    "Sanguijuela Colosal",
    "Espantajo Anegado",
    "Ahogado Errante",
    "Chamán del Cieno",
    "Cangrejo Acorazado",
    "Serpiente de Fango",
    "Sacerdote Ahogado",
    "Horror de Profundidad",
    "Guardián del Templo Hundido",
    "El Anegado",
}


def test_every_backbone_enemy_scores_without_error_and_is_documented():
    for name in ENEMY_PROGRESSION:
        zone_id = zone_for_enemy(name)
        assert zone_id is not None, name
        enemy = _get_enemy_instance(name)
        actual = power_score(enemy.stats)
        lo, hi = zone_score_range(_ZONE_INDEX[zone_id])
        in_range = lo <= actual <= hi
        if name not in _KNOWN_OUT_OF_RANGE:
            assert in_range, f"{name}: poder {actual:.0f} fuera del rango de su zona [{lo:.0f}, {hi:.0f}]"
        else:
            assert not in_range, f"{name} ya no está fuera de rango: ¿hay que sacarlo de _KNOWN_OUT_OF_RANGE?"


def test_los_yermos_tiered_enemies_are_within_the_design_tolerance_or_documented():
    """Los Yermos es la única zona con tiers ya fijados por el GDD: comprueba la
    predicción exacta objetivo(zona, tier), no solo el rango [1, 10]. Solo Huargo
    cae dentro del ±10%; Goblin (+15%, ambigüedad de redondeo de las constantes),
    Esqueleto (-36%, la reanimación no entra en la fórmula) y Bandido (+44%,
    emboscada + desarme tampoco) se quedan fuera — documentado, no corregido
    aquí (ese es el trabajo de rebalanceo aparte que ya sigue TODO.md)."""
    zone_index = _ZONE_INDEX["los_yermos"]
    within_tolerance = {"Huargo"}

    for name, tier in _YERMOS_TIERS.items():
        actual = power_score(_get_enemy_instance(name).stats)
        target = target_score(zone_index, tier)
        dev = deviation(actual, target)
        if name in within_tolerance:
            assert abs(dev) <= DESIGN_TOLERANCE, f"{name}: {dev:+.0%}, se esperaba dentro de ±{DESIGN_TOLERANCE:.0%}"
        else:
            assert abs(dev) > DESIGN_TOLERANCE, f"{name} ya está dentro de tolerancia: revisa este test"
