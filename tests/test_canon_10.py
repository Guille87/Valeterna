"""Cañón del Trueno a 10 enemigos (v0.15.0-a, GDD §3/§4): mecánicas propias de
los 8 enemigos nuevos, insertados en la cadena tras Gárgola y Gólem de Piedra
(ya existentes, sin cambios de mecánica). Sigue la convención del resto de
`test_*_10.py`: las tiradas se prueban llamando a los métodos internos
directamente en vez de a `perform_turn()` completo, para no tener que
encadenar varias tiradas de `random.random()` compartido (ver CLAUDE.md,
"Testing conventions")."""

from valeterna.characters.enemies.aparicion_de_la_cuadrilla import AparicionDeLaCuadrilla
from valeterna.characters.enemies.cabra_montes_corrupta import CabraMontesCorrupta
from valeterna.characters.enemies.chispa_del_puntal import ChispaDelPuntal
from valeterna.characters.enemies.el_decimoquinto import ElDecimoquinto
from valeterna.characters.enemies.gargola import Gargola
from valeterna.characters.enemies.golem import GolemDePiedra
from valeterna.characters.enemies.heraldo_de_la_tormenta import HeraldoDeLaTormenta
from valeterna.characters.enemies.minero_poseido import MineroPoseido
from valeterna.characters.enemies.murcielago_de_tormenta import MurcielagoDeTormenta
from valeterna.characters.enemies.verdugo_de_la_mina import VerdugoDeLaMina
from valeterna.characters.power_budget import power_score
from valeterna.combat.battle import ENEMY_PROGRESSION

# --- Cadena de desbloqueo -------------------------------------------------------


def test_canon_chain_gates_the_guardian_before_the_torre():
    assert ENEMY_PROGRESSION["Gólem de Piedra"] == "Minero Poseído"
    assert ENEMY_PROGRESSION["Minero Poseído"] == "Murciélago de Tormenta"
    assert ENEMY_PROGRESSION["Murciélago de Tormenta"] == "Chispa del Puntal"
    assert ENEMY_PROGRESSION["Chispa del Puntal"] == "Aparición de la Cuadrilla"
    assert ENEMY_PROGRESSION["Aparición de la Cuadrilla"] == "Verdugo de la Mina"
    assert ENEMY_PROGRESSION["Verdugo de la Mina"] == "Cabra Montés Corrupta"
    assert ENEMY_PROGRESSION["Cabra Montés Corrupta"] == "Heraldo de la Tormenta"
    assert ENEMY_PROGRESSION["Heraldo de la Tormenta"] == "El Decimoquinto"
    assert ENEMY_PROGRESSION["El Decimoquinto"] == "Mago"  # el guardián abre la Torre de los Arcanos/Necrópolis


def test_canon_progression_is_increasingly_powerful():
    """Dificultad progresiva: cada enemigo nuevo supera en poder real al
    anterior de la cadena, empezando por Gólem de Piedra (ya implementado)."""
    chain = [
        GolemDePiedra(),
        MineroPoseido(),
        MurcielagoDeTormenta(),
        ChispaDelPuntal(),
        AparicionDeLaCuadrilla(),
        VerdugoDeLaMina(),
        CabraMontesCorrupta(),
        HeraldoDeLaTormenta(),
        ElDecimoquinto(),
    ]
    scores = [power_score(enemy.stats) for enemy in chain]
    assert scores == sorted(scores)
    assert len(set(scores)) == len(scores)  # estrictamente creciente, sin empates


def test_gargola_was_reinforced_ahead_of_the_new_roster():
    """Gárgola se reforzó en v0.14.0-f para abrir hueco a la Ciénaga; sigue
    por debajo de Gólem de Piedra, que a su vez queda por debajo de todo el
    roster nuevo del Cañón."""
    assert power_score(Gargola().stats) < power_score(GolemDePiedra().stats)


# --- Minero Poseído: sangrado al golpear ------------------------------------------


def test_minero_poseido_can_bleed_on_hit(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.enemies.minero_poseido.random.random", lambda: 0.0)
    player.stats.evasion = 0

    MineroPoseido().perform_turn(player)

    assert any(e["name"] == "sangrado" for e in player.status_effects)


def test_minero_poseido_does_not_always_bleed(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)  # acierta el golpe
    monkeypatch.setattr("valeterna.characters.enemies.minero_poseido.random.random", lambda: 0.99)  # sin sangrado
    player.stats.evasion = 0

    MineroPoseido().perform_turn(player)

    assert not any(e["name"] == "sangrado" for e in player.status_effects)


# --- Murciélago de Tormenta: doble ataque -----------------------------------------


def test_murcielago_de_tormenta_can_add_a_second_swoop(player, monkeypatch):
    """Mismo patrón que el Enjambre de Polillas Pálidas / Serpiente de Fango:
    acierto 1er golpe -> crítico (no) -> segundo revoloteo (sí) -> acierto 2º
    golpe (sin veneno que tirar aquí, este enemigo no inflige nada)."""
    monkeypatch.setattr("valeterna.characters.enemies.enemy_base.random.randint", lambda a, b: 20)
    rolls = iter([0.5, 0.5, 0.0, 0.5])
    monkeypatch.setattr("valeterna.characters.enemies.murcielago_de_tormenta.random.random", lambda: next(rolls))
    player.stats.evasion = 0
    player.stats.armor = 0

    before = player.stats.health
    MurcielagoDeTormenta().perform_turn(player)
    dealt = before - player.stats.health

    assert dealt == 30  # 20 del primer golpe + 10 (mitad) del segundo


def test_murcielago_de_tormenta_second_swoop_is_not_guaranteed(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.enemies.enemy_base.random.randint", lambda a, b: 20)
    rolls = iter([0.5, 0.5, 0.99])  # acierto -> sin crítico -> sin segundo revoloteo
    monkeypatch.setattr("valeterna.characters.enemies.murcielago_de_tormenta.random.random", lambda: next(rolls))
    player.stats.evasion = 0
    player.stats.armor = 0

    before = player.stats.health
    MurcielagoDeTormenta().perform_turn(player)
    dealt = before - player.stats.health

    assert dealt == 20  # solo el primer golpe


# --- Chispa del Puntal: descarga con parálisis ------------------------------------


def test_chispa_del_puntal_can_paralyze_on_hit(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)  # acierta y critea
    monkeypatch.setattr("valeterna.characters.enemies.chispa_del_puntal.random.random", lambda: 0.0)  # paraliza
    player.stats.evasion = 0
    player.stats.armor = 0

    ChispaDelPuntal().perform_turn(player)

    assert any(e["name"] == "paralizado" for e in player.status_effects)


def test_chispa_del_puntal_is_immune_to_its_own_element():
    chispa = ChispaDelPuntal()
    assert "rayo" in chispa.IMMUNE_ELEMENTS
    assert "paralizado" in chispa.IMMUNE_STATUSES


# --- Aparición de la Cuadrilla: emboscada tras la primera derrota ----------------


def test_aparicion_de_la_cuadrilla_ambushes_only_after_being_defeated_once(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.enemies.aparicion_de_la_cuadrilla.random.random", lambda: 0.0)
    player.stats.evasion = 0
    aparicion = AparicionDeLaCuadrilla()

    assert aparicion.check_ambush(player, defeated_enemies=[]) is False
    assert aparicion.check_ambush(player, defeated_enemies=["Aparición de la Cuadrilla"]) is True
    assert aparicion.check_ambush(player, defeated_enemies=["Aparición de la Cuadrilla"]) is False


# --- Verdugo de la Mina: derrumbe inesquivable ------------------------------------


def test_verdugo_de_la_mina_cave_in_cannot_be_dodged(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.enemies.enemy_base.random.randint", lambda a, b: 15)
    player.stats.evasion = 999
    player.stats.armor = 0

    before = player.stats.health
    VerdugoDeLaMina()._cave_in(player)

    assert player.stats.health < before


# --- Cabra Montés Corrupta: topetazo aturdidor ------------------------------------


def test_cabra_montes_corrupta_headbutt_can_stun(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)  # acierta
    monkeypatch.setattr("valeterna.characters.enemies.cabra_montes_corrupta.random.random", lambda: 0.0)  # aturde
    player.stats.evasion = 0
    player.stats.armor = 0

    CabraMontesCorrupta()._headbutt(player)

    assert any(e["name"] == "aturdido" for e in player.status_effects)


# --- Heraldo de la Tormenta: autocuración, maldición y rayo -----------------------


def test_heraldo_de_la_tormenta_heals_itself_below_half_health():
    heraldo = HeraldoDeLaTormenta()
    heraldo.stats.health = 10

    heraldo._self_heal()

    assert heraldo.stats.health > 10


def test_heraldo_de_la_tormenta_curse_reduces_armor_until_it_expires(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.enemies.heraldo_de_la_tormenta.random.random", lambda: 0.0)
    player.stats.armor = 8
    player.stats.evasion = 0

    HeraldoDeLaTormenta()._cast_curse(player)

    assert any(e["name"] == "maldicion" for e in player.status_effects)
    assert player.get_total_armor() == 4  # 8 - power(4)


def test_heraldo_de_la_tormenta_bolt_deals_lightning_damage(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)  # acierta y critea
    player.stats.evasion = 0
    player.stats.armor = 0

    before = player.stats.health
    HeraldoDeLaTormenta()._storm_bolt(player)

    assert player.stats.health < before


# --- El Decimoquinto: guardián, autocuración y parálisis --------------------------


def test_el_decimoquinto_is_marked_as_the_canons_guardian():
    guardian = ElDecimoquinto()
    assert guardian.ENCOUNTER_KIND == "guardian"
    assert guardian.ENCOUNTER_LINE
    assert guardian.TAUNT_LINES


def test_el_decimoquinto_heals_itself_below_40_percent_health():
    guardian = ElDecimoquinto()
    guardian.stats.health = int(guardian.stats.max_health * 0.39)

    guardian._self_heal()

    assert guardian.stats.health > int(guardian.stats.max_health * 0.39)


def test_el_decimoquinto_lightning_strike_can_paralyze_on_hit(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)  # acierta y critea
    monkeypatch.setattr("valeterna.characters.enemies.el_decimoquinto.random.random", lambda: 0.0)  # paraliza
    player.stats.evasion = 0
    player.stats.armor = 0

    ElDecimoquinto()._lightning_strike(player)

    assert any(e["name"] == "paralizado" for e in player.status_effects)
