"""Ciénaga de los Ahogados a 10 enemigos (v0.14.0-f, GDD §3/§4): mecánicas
propias de los 10 enemigos nuevos, insertados en la cadena entre El Enraizado
(guardián del Bosque) y Gárgola (ahora guardián reforzado que abre el Cañón
del Trueno). Sigue la convención del resto de `test_*_10.py`: las tiradas se
prueban llamando a los métodos internos directamente en vez de a
`perform_turn()` completo, para no tener que encadenar varias tiradas de
`random.random()` compartido (ver CLAUDE.md, "Testing conventions")."""

from valeterna.characters.enemies.ahogado_errante import AhogadoErrante
from valeterna.characters.enemies.cangrejo_acorazado import CangrejoAcorazado
from valeterna.characters.enemies.chaman_del_cieno import ChamanDelCieno
from valeterna.characters.enemies.el_anegado import ElAnegado
from valeterna.characters.enemies.espantajo_anegado import EspantajoAnegado
from valeterna.characters.enemies.gargola import Gargola
from valeterna.characters.enemies.guardian_del_templo_hundido import GuardianDelTemploHundido
from valeterna.characters.enemies.horror_de_profundidad import HorrorDeProfundidad
from valeterna.characters.enemies.sacerdote_ahogado import SacerdoteAhogado
from valeterna.characters.enemies.sanguijuela_colosal import SanguijuelaColosal
from valeterna.characters.enemies.serpiente_de_fango import SerpienteDeFango
from valeterna.characters.power_budget import power_score
from valeterna.combat.battle import ENEMY_PROGRESSION

# --- Cadena de desbloqueo -------------------------------------------------------


def test_cienaga_chain_gates_the_guardian_before_the_canon():
    assert ENEMY_PROGRESSION["El Enraizado"] == "Sanguijuela Colosal"
    assert ENEMY_PROGRESSION["Sanguijuela Colosal"] == "Espantajo Anegado"
    assert ENEMY_PROGRESSION["Espantajo Anegado"] == "Ahogado Errante"
    assert ENEMY_PROGRESSION["Ahogado Errante"] == "Chamán del Cieno"
    assert ENEMY_PROGRESSION["Chamán del Cieno"] == "Cangrejo Acorazado"
    assert ENEMY_PROGRESSION["Cangrejo Acorazado"] == "Serpiente de Fango"
    assert ENEMY_PROGRESSION["Serpiente de Fango"] == "Sacerdote Ahogado"
    assert ENEMY_PROGRESSION["Sacerdote Ahogado"] == "Horror de Profundidad"
    assert ENEMY_PROGRESSION["Horror de Profundidad"] == "Guardián del Templo Hundido"
    assert ENEMY_PROGRESSION["Guardián del Templo Hundido"] == "El Anegado"
    assert ENEMY_PROGRESSION["El Anegado"] == "Gárgola"  # el guardián de la Ciénaga abre el Cañón del Trueno


def test_cienaga_progression_is_increasingly_powerful():
    """Dificultad progresiva (petición explícita del usuario): cada enemigo
    nuevo supera en poder real al anterior de la cadena, y Gárgola (reforzada
    en la misma sub-fase) queda por encima de El Anegado."""
    chain = [
        SanguijuelaColosal(),
        EspantajoAnegado(),
        AhogadoErrante(),
        ChamanDelCieno(),
        CangrejoAcorazado(),
        SerpienteDeFango(),
        SacerdoteAhogado(),
        HorrorDeProfundidad(),
        GuardianDelTemploHundido(),
        ElAnegado(),
        Gargola(),
    ]
    scores = [power_score(enemy.stats) for enemy in chain]
    assert scores == sorted(scores)
    assert len(set(scores)) == len(scores)  # estrictamente creciente, sin empates


# --- Sanguijuela Colosal: vida robada ---------------------------------------------


def test_sanguijuela_colosal_heals_from_a_fraction_of_the_damage_it_deals(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.99)  # acierta, sin crítico
    monkeypatch.setattr("valeterna.characters.enemies.enemy_base.random.randint", lambda a, b: 20)
    player.stats.evasion = 0
    player.stats.armor = 0

    sanguijuela = SanguijuelaColosal()
    sanguijuela.stats.health = 10

    sanguijuela.perform_turn(player)

    assert sanguijuela.stats.health > 10


# --- Espantajo Anegado: sangrado al golpear ---------------------------------------


def test_espantajo_anegado_can_bleed_on_hit(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.enemies.espantajo_anegado.random.random", lambda: 0.0)
    player.stats.evasion = 0

    EspantajoAnegado().perform_turn(player)

    assert any(e["name"] == "sangrado" for e in player.status_effects)


def test_espantajo_anegado_does_not_always_bleed(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)  # acierta el golpe
    monkeypatch.setattr("valeterna.characters.enemies.espantajo_anegado.random.random", lambda: 0.99)  # sin sangrado
    player.stats.evasion = 0

    EspantajoAnegado().perform_turn(player)

    assert not any(e["name"] == "sangrado" for e in player.status_effects)


# --- Ahogado Errante: emboscada tras la primera derrota ---------------------------


def test_ahogado_errante_ambushes_only_after_being_defeated_once(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.enemies.ahogado_errante.random.random", lambda: 0.0)
    player.stats.evasion = 0
    ahogado = AhogadoErrante()

    assert ahogado.check_ambush(player, defeated_enemies=[]) is False  # nunca derrotado: sin emboscada
    assert ahogado.check_ambush(player, defeated_enemies=["Ahogado Errante"]) is True
    assert ahogado.check_ambush(player, defeated_enemies=["Ahogado Errante"]) is False  # solo una vez por combate


# --- Chamán del Cieno: autocuración, maldición y grumo de cieno -------------------


def test_chaman_del_cieno_heals_itself_below_half_health():
    chaman = ChamanDelCieno()
    chaman.stats.health = 10

    chaman._self_heal()

    assert chaman.stats.health > 10


def test_chaman_del_cieno_curse_reduces_armor_until_it_expires(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.enemies.chaman_del_cieno.random.random", lambda: 0.0)
    player.stats.armor = 6
    player.stats.evasion = 0

    ChamanDelCieno()._cast_curse(player)

    assert any(e["name"] == "maldicion" for e in player.status_effects)
    assert player.get_total_armor() == 3  # 6 - power(3)


def test_chaman_del_cieno_bolt_deals_magical_darkness_damage(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)  # acierta y critea
    player.stats.evasion = 0
    player.stats.magic_resist = 0

    before = player.stats.health
    ChamanDelCieno()._sludge_bolt(player)

    assert player.stats.health < before


# --- Cangrejo Acorazado: tenaza inesquivable --------------------------------------


def test_cangrejo_acorazado_pincer_crush_cannot_be_dodged(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.enemies.enemy_base.random.randint", lambda a, b: 15)
    player.stats.evasion = 999  # aun con evasión altísima, no hay tirada de acierto que falle
    player.stats.armor = 0

    before = player.stats.health
    CangrejoAcorazado()._pincer_crush(player)

    assert player.stats.health < before


# --- Serpiente de Fango: doble mordisco y veneno ----------------------------------


def test_serpiente_de_fango_can_add_a_second_bite(player, monkeypatch):
    """Mismo patrón que el Enjambre de Polillas Pálidas: orden real de tiradas
    para un turno con segundo mordisco: acierto 1er golpe -> crítico (no) ->
    veneno 1er golpe (no) -> segundo mordisco (sí) -> acierto 2º golpe ->
    veneno 2º golpe (no)."""
    monkeypatch.setattr("valeterna.characters.enemies.enemy_base.random.randint", lambda a, b: 20)
    rolls = iter([0.5, 0.5, 0.99, 0.0, 0.5, 0.99])
    monkeypatch.setattr("valeterna.characters.enemies.serpiente_de_fango.random.random", lambda: next(rolls))
    player.stats.evasion = 0
    player.stats.armor = 0

    before = player.stats.health
    SerpienteDeFango().perform_turn(player)
    dealt = before - player.stats.health

    assert dealt == 30  # 20 del primer mordisco + 10 (mitad) del segundo


def test_serpiente_de_fango_second_bite_is_not_guaranteed(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.enemies.enemy_base.random.randint", lambda a, b: 20)
    rolls = iter([0.5, 0.5, 0.99, 0.99])  # acierto -> sin crítico -> sin veneno -> sin segundo mordisco
    monkeypatch.setattr("valeterna.characters.enemies.serpiente_de_fango.random.random", lambda: next(rolls))
    player.stats.evasion = 0
    player.stats.armor = 0

    before = player.stats.health
    SerpienteDeFango().perform_turn(player)
    dealt = before - player.stats.health

    assert dealt == 20  # solo el primer mordisco
    assert not any(e["name"] == "veneno" for e in player.status_effects)


# --- Sacerdote Ahogado: confusión y rezo corrupto ---------------------------------


def test_sacerdote_ahogado_can_confuse_instead_of_attacking(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.enemies.sacerdote_ahogado.random.random", lambda: 0.0)
    player.stats.evasion = 0

    SacerdoteAhogado()._cast_confusion(player)

    assert any(e["name"] == "confusion" for e in player.status_effects)


def test_sacerdote_ahogado_chant_deals_magical_darkness_damage(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)  # acierta y critea
    player.stats.evasion = 0
    player.stats.magic_resist = 0

    before = player.stats.health
    SacerdoteAhogado()._dark_chant(player)

    assert player.stats.health < before


# --- Horror de Profundidad: coletazo aturdidor ------------------------------------


def test_horror_de_profundidad_tail_slam_can_stun(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)  # acierta
    monkeypatch.setattr("valeterna.characters.enemies.horror_de_profundidad.random.random", lambda: 0.0)  # aturde
    player.stats.evasion = 0
    player.stats.armor = 0

    HorrorDeProfundidad()._tail_slam(player)

    assert any(e["name"] == "aturdido" for e in player.status_effects)


# --- Guardián del Templo Hundido: golpe de piedra inesquivable --------------------


def test_guardian_del_templo_hundido_stone_strike_cannot_be_dodged(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.enemies.enemy_base.random.randint", lambda a, b: 15)
    player.stats.evasion = 999
    player.stats.armor = 0

    before = player.stats.health
    GuardianDelTemploHundido()._stone_strike(player)

    assert player.stats.health < before


# --- El Anegado: guardián, autocuración y maldición -------------------------------


def test_el_anegado_is_marked_as_the_cienagas_guardian():
    guardian = ElAnegado()
    assert guardian.ENCOUNTER_KIND == "guardian"
    assert guardian.ENCOUNTER_LINE
    assert guardian.TAUNT_LINES


def test_el_anegado_heals_itself_below_40_percent_health():
    guardian = ElAnegado()
    guardian.stats.health = int(guardian.stats.max_health * 0.39)

    guardian._self_heal()

    assert guardian.stats.health > int(guardian.stats.max_health * 0.39)


def test_el_anegado_drowned_strike_can_curse_on_hit(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)  # acierta y critea
    monkeypatch.setattr("valeterna.characters.enemies.el_anegado.random.random", lambda: 0.0)  # maldice
    player.stats.evasion = 0
    player.stats.magic_resist = 0
    player.stats.armor = 5

    ElAnegado()._drowned_strike(player)

    assert any(e["name"] == "maldicion" for e in player.status_effects)
