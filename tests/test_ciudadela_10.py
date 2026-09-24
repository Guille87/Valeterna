"""Ciudadela en Ruinas a 10 enemigos (v0.15.0-c, GDD §3/§4): mecánicas propias
de los 8 enemigos nuevos, insertados en la cadena tras Ángel Caído y Demonio
(ya existentes, sin cambios de mecánica) y antes del Dragón, reforzado en esta
misma sub-fase. Sigue la convención del resto de `test_*_10.py`: las tiradas
se prueban llamando a los métodos internos directamente en vez de a
`perform_turn()` completo, para no tener que encadenar varias tiradas de
`random.random()` compartido (ver CLAUDE.md, "Testing conventions")."""

from valeterna.characters.enemies.ciudadano_hueco import CiudadanoHueco
from valeterna.characters.enemies.custodio_de_vidrieras import CustodioDeVidrieras
from valeterna.characters.enemies.demonio import Demonio
from valeterna.characters.enemies.dragon import Dragon
from valeterna.characters.enemies.eco_de_la_guardia import EcoDeLaGuardia
from valeterna.characters.enemies.el_sin_rostro import ElSinRostro
from valeterna.characters.enemies.guardia_caida import GuardiaCaida
from valeterna.characters.enemies.heraldo_del_amo import HeraldoDelAmo
from valeterna.characters.enemies.serafin_corrupto import SerafinCorrupto
from valeterna.characters.enemies.verdugo_infernal import VerdugoInfernal
from valeterna.characters.power_budget import power_score
from valeterna.combat.battle import ENEMY_PROGRESSION

# --- Cadena de desbloqueo -------------------------------------------------------


def test_ciudadela_chain_gates_the_guardian_before_el_corazon():
    assert ENEMY_PROGRESSION["Demonio"] == "Ciudadano Hueco"
    assert ENEMY_PROGRESSION["Ciudadano Hueco"] == "Guardia Caída"
    assert ENEMY_PROGRESSION["Guardia Caída"] == "Serafín Corrupto"
    assert ENEMY_PROGRESSION["Serafín Corrupto"] == "Eco de la Guardia"
    assert ENEMY_PROGRESSION["Eco de la Guardia"] == "Custodio de Vidrieras"
    assert ENEMY_PROGRESSION["Custodio de Vidrieras"] == "Verdugo Infernal"
    assert ENEMY_PROGRESSION["Verdugo Infernal"] == "Heraldo del Amo"
    assert ENEMY_PROGRESSION["Heraldo del Amo"] == "El Sin Rostro"
    assert ENEMY_PROGRESSION["El Sin Rostro"] == "Dragón"  # el guardián abre El Corazón de la Brecha


def test_ciudadela_progression_is_increasingly_powerful():
    """Dificultad progresiva: cada enemigo nuevo supera en poder real al
    anterior de la cadena, empezando por Demonio (ya implementado)."""
    chain = [
        Demonio(),
        CiudadanoHueco(),
        GuardiaCaida(),
        SerafinCorrupto(),
        EcoDeLaGuardia(),
        CustodioDeVidrieras(),
        VerdugoInfernal(),
        HeraldoDelAmo(),
        ElSinRostro(),
    ]
    scores = [power_score(enemy.stats) for enemy in chain]
    assert scores == sorted(scores)
    assert len(set(scores)) == len(scores)  # estrictamente creciente, sin empates


def test_dragon_was_reinforced_ahead_of_the_new_roster():
    """El Dragón se reforzó en v0.15.0-c para abrir hueco al roster nuevo de
    la Ciudadela; sigue por encima de El Sin Rostro."""
    assert power_score(ElSinRostro().stats) < power_score(Dragon().stats)


# --- Ciudadano Hueco: desarme al golpear ------------------------------------------


def test_ciudadano_hueco_can_disarm_on_hit(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.enemies.ciudadano_hueco.random.random", lambda: 0.0)
    player.stats.evasion = 0

    CiudadanoHueco().perform_turn(player)

    assert any(e["name"] == "desarmado" for e in player.status_effects)


def test_ciudadano_hueco_does_not_always_disarm(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)  # acierta el golpe
    monkeypatch.setattr("valeterna.characters.enemies.ciudadano_hueco.random.random", lambda: 0.99)  # sin desarme
    player.stats.evasion = 0

    CiudadanoHueco().perform_turn(player)

    assert not any(e["name"] == "desarmado" for e in player.status_effects)


# --- Guardia Caída: segunda estocada -----------------------------------------------


def test_guardia_caida_can_add_a_second_strike(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.enemies.enemy_base.random.randint", lambda a, b: 20)
    rolls = iter([0.5, 0.5, 0.0, 0.5])
    monkeypatch.setattr("valeterna.characters.enemies.guardia_caida.random.random", lambda: next(rolls))
    player.stats.evasion = 0
    player.stats.armor = 0

    before = player.stats.health
    GuardiaCaida().perform_turn(player)
    dealt = before - player.stats.health

    assert dealt == 30  # 20 de la primera estocada + 10 (mitad) de la segunda


def test_guardia_caida_second_strike_is_not_guaranteed(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.enemies.enemy_base.random.randint", lambda a, b: 20)
    rolls = iter([0.5, 0.5, 0.99])
    monkeypatch.setattr("valeterna.characters.enemies.guardia_caida.random.random", lambda: next(rolls))
    player.stats.evasion = 0
    player.stats.armor = 0

    before = player.stats.health
    GuardiaCaida().perform_turn(player)
    dealt = before - player.stats.health

    assert dealt == 20  # solo la primera estocada


# --- Serafín Corrupto: autocuración, maldición y gracia invertida -----------------


def test_serafin_corrupto_heals_itself_below_half_health():
    serafin = SerafinCorrupto()
    serafin.stats.health = 10

    serafin._self_heal()

    assert serafin.stats.health > 10


def test_serafin_corrupto_curse_reduces_armor_until_it_expires(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.enemies.serafin_corrupto.random.random", lambda: 0.0)
    player.stats.armor = 9
    player.stats.evasion = 0

    SerafinCorrupto()._cast_curse(player)

    assert any(e["name"] == "maldicion" for e in player.status_effects)
    assert player.get_total_armor() == 5  # 9 - power(4)


def test_serafin_corrupto_bolt_deals_magical_darkness_damage(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)  # acierta y critea
    player.stats.evasion = 0
    player.stats.magic_resist = 0

    before = player.stats.health
    SerafinCorrupto()._dark_grace(player)

    assert player.stats.health < before


# --- Eco de la Guardia: emboscada tras la primera derrota -------------------------


def test_eco_de_la_guardia_ambushes_only_after_being_defeated_once(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.enemies.eco_de_la_guardia.random.random", lambda: 0.0)
    player.stats.evasion = 0
    eco = EcoDeLaGuardia()

    assert eco.check_ambush(player, defeated_enemies=[]) is False
    assert eco.check_ambush(player, defeated_enemies=["Eco de la Guardia"]) is True
    assert eco.check_ambush(player, defeated_enemies=["Eco de la Guardia"]) is False


# --- Custodio de Vidrieras: confusión y luz astillada -----------------------------


def test_custodio_de_vidrieras_can_confuse_instead_of_attacking(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.enemies.custodio_de_vidrieras.random.random", lambda: 0.0)
    player.stats.evasion = 0

    CustodioDeVidrieras()._glass_gaze(player)

    assert any(e["name"] == "confusion" for e in player.status_effects)


def test_custodio_de_vidrieras_bolt_deals_magical_holy_damage(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)  # acierta y critea
    player.stats.evasion = 0
    player.stats.magic_resist = 0

    before = player.stats.health
    CustodioDeVidrieras()._shattered_light(player)

    assert player.stats.health < before


# --- Verdugo Infernal: vida robada -------------------------------------------------


def test_verdugo_infernal_heals_from_a_fraction_of_the_damage_it_deals(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.99)  # acierta, sin crítico
    monkeypatch.setattr("valeterna.characters.enemies.enemy_base.random.randint", lambda a, b: 20)
    player.stats.evasion = 0
    player.stats.armor = 0

    verdugo = VerdugoInfernal()
    verdugo.stats.health = 10

    verdugo.perform_turn(player)

    assert verdugo.stats.health > 10


# --- Heraldo del Amo: proclama inevitable ------------------------------------------


def test_heraldo_del_amo_proclamation_cannot_be_dodged(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.enemies.enemy_base.random.randint", lambda a, b: 15)
    player.stats.evasion = 999
    player.stats.armor = 0

    before = player.stats.health
    HeraldoDelAmo()._proclamation(player)

    assert player.stats.health < before


# --- El Sin Rostro: guardián, autocuración y maldición ----------------------------


def test_el_sin_rostro_is_marked_as_the_ciudadelas_guardian():
    guardian = ElSinRostro()
    assert guardian.ENCOUNTER_KIND == "guardian"
    assert guardian.ENCOUNTER_LINE
    assert guardian.TAUNT_LINES


def test_el_sin_rostro_heals_itself_below_40_percent_health():
    guardian = ElSinRostro()
    guardian.stats.health = int(guardian.stats.max_health * 0.39)

    guardian._self_heal()

    assert guardian.stats.health > int(guardian.stats.max_health * 0.39)


def test_el_sin_rostro_ruin_bolt_can_curse_on_hit(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)  # acierta y critea
    monkeypatch.setattr("valeterna.characters.enemies.el_sin_rostro.random.random", lambda: 0.0)  # maldice
    player.stats.evasion = 0
    player.stats.magic_resist = 0
    player.stats.armor = 7

    ElSinRostro()._ruin_bolt(player)

    assert any(e["name"] == "maldicion" for e in player.status_effects)
