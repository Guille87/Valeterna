"""Torre de los Arcanos / Necrópolis a 10 enemigos (v0.15.0-b, GDD §3/§4): mecánicas
propias de los 8 enemigos nuevos, insertados en la cadena tras Mago y
Nigromante (ya existentes, sin cambios de mecánica). Sigue la convención del
resto de `test_*_10.py`: las tiradas se prueban llamando a los métodos
internos directamente en vez de a `perform_turn()` completo, para no tener
que encadenar varias tiradas de `random.random()` compartido (ver CLAUDE.md,
"Testing conventions")."""

from valeterna.characters.enemies.bibliotecario_errante import BibliotecarioErrante
from valeterna.characters.enemies.carronero_de_cripta import CarroneroDeCripta
from valeterna.characters.enemies.custodio_arcano import CustodioArcano
from valeterna.characters.enemies.el_archivista import ElArchivista
from valeterna.characters.enemies.espectro_de_la_guardia import EspectroDeLaGuardia
from valeterna.characters.enemies.guardian_del_tomo_prohibido import GuardianDelTomoProhibido
from valeterna.characters.enemies.guardian_osario import GuardianOsario
from valeterna.characters.enemies.mage import Mago
from valeterna.characters.enemies.nigromante import Nigromante
from valeterna.characters.enemies.tomo_viviente import TomoViviente
from valeterna.characters.power_budget import power_score
from valeterna.combat.battle import ENEMY_PROGRESSION

# --- Cadena de desbloqueo -------------------------------------------------------


def test_torre_chain_gates_the_guardian_before_the_ciudadela():
    assert ENEMY_PROGRESSION["Mago"] == "Nigromante"
    assert ENEMY_PROGRESSION["Nigromante"] == "Tomo Viviente"
    assert ENEMY_PROGRESSION["Tomo Viviente"] == "Guardián Osario"
    assert ENEMY_PROGRESSION["Guardián Osario"] == "Custodio Arcano"
    assert ENEMY_PROGRESSION["Custodio Arcano"] == "Espectro de la Guardia"
    assert ENEMY_PROGRESSION["Espectro de la Guardia"] == "Bibliotecario Errante"
    assert ENEMY_PROGRESSION["Bibliotecario Errante"] == "Carroñero de Cripta"
    assert ENEMY_PROGRESSION["Carroñero de Cripta"] == "Guardián del Tomo Prohibido"
    assert ENEMY_PROGRESSION["Guardián del Tomo Prohibido"] == "El Archivista"
    assert ENEMY_PROGRESSION["El Archivista"] == "Ángel Caído"  # el guardián abre la Ciudadela en Ruinas


def test_torre_progression_is_increasingly_powerful():
    """Dificultad progresiva: cada enemigo nuevo supera en poder real al
    anterior de la cadena, empezando por Nigromante (ya implementado)."""
    chain = [
        Nigromante(),
        TomoViviente(),
        GuardianOsario(),
        CustodioArcano(),
        EspectroDeLaGuardia(),
        BibliotecarioErrante(),
        CarroneroDeCripta(),
        GuardianDelTomoProhibido(),
        ElArchivista(),
    ]
    scores = [power_score(enemy.stats) for enemy in chain]
    assert scores == sorted(scores)
    assert len(set(scores)) == len(scores)  # estrictamente creciente, sin empates


def test_mago_is_a_known_low_power_outlier_ahead_of_the_new_roster():
    """Mago (punto ciego documentado de la fórmula) sigue muy por debajo de
    Nigromante y de todo el roster nuevo; no se tocó su diseño."""
    assert power_score(Mago().stats) < power_score(Nigromante().stats)


# --- Tomo Viviente: sangrado al golpear -------------------------------------------


def test_tomo_viviente_can_bleed_on_hit(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.enemies.tomo_viviente.random.random", lambda: 0.0)
    player.stats.evasion = 0

    TomoViviente().perform_turn(player)

    assert any(e["name"] == "sangrado" for e in player.status_effects)


def test_tomo_viviente_does_not_always_bleed(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)  # acierta el golpe
    monkeypatch.setattr("valeterna.characters.enemies.tomo_viviente.random.random", lambda: 0.99)  # sin sangrado
    player.stats.evasion = 0

    TomoViviente().perform_turn(player)

    assert not any(e["name"] == "sangrado" for e in player.status_effects)


# --- Guardián Osario: segundo golpe de púas ---------------------------------------


def test_guardian_osario_can_add_a_second_strike(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.enemies.enemy_base.random.randint", lambda a, b: 20)
    rolls = iter([0.5, 0.5, 0.0, 0.5])
    monkeypatch.setattr("valeterna.characters.enemies.guardian_osario.random.random", lambda: next(rolls))
    player.stats.evasion = 0
    player.stats.armor = 0

    before = player.stats.health
    GuardianOsario().perform_turn(player)
    dealt = before - player.stats.health

    assert dealt == 30  # 20 del primer golpe + 10 (mitad) del segundo


def test_guardian_osario_second_strike_is_not_guaranteed(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.enemies.enemy_base.random.randint", lambda a, b: 20)
    rolls = iter([0.5, 0.5, 0.99])
    monkeypatch.setattr("valeterna.characters.enemies.guardian_osario.random.random", lambda: next(rolls))
    player.stats.evasion = 0
    player.stats.armor = 0

    before = player.stats.health
    GuardianOsario().perform_turn(player)
    dealt = before - player.stats.health

    assert dealt == 20  # solo el primer golpe


# --- Custodio Arcano: autocuración y dardo arcano ---------------------------------


def test_custodio_arcano_heals_itself_below_half_health():
    custodio = CustodioArcano()
    custodio.stats.health = 10

    custodio._self_heal()

    assert custodio.stats.health > 10


def test_custodio_arcano_bolt_deals_magical_arcane_damage(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)  # acierta y critea
    player.stats.evasion = 0
    player.stats.magic_resist = 0

    before = player.stats.health
    CustodioArcano()._arcane_bolt(player)

    assert player.stats.health < before


def test_custodio_arcano_is_immune_to_poison():
    custodio = CustodioArcano()
    assert "veneno" in custodio.IMMUNE_ELEMENTS
    assert "veneno" in custodio.IMMUNE_STATUSES


# --- Espectro de la Guardia: emboscada tras la primera derrota -------------------


def test_espectro_de_la_guardia_ambushes_only_after_being_defeated_once(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.enemies.espectro_de_la_guardia.random.random", lambda: 0.0)
    player.stats.evasion = 0
    espectro = EspectroDeLaGuardia()

    assert espectro.check_ambush(player, defeated_enemies=[]) is False
    assert espectro.check_ambush(player, defeated_enemies=["Espectro de la Guardia"]) is True
    assert espectro.check_ambush(player, defeated_enemies=["Espectro de la Guardia"]) is False


# --- Bibliotecario Errante: confusión y dardo arcano ------------------------------


def test_bibliotecario_errante_can_confuse_instead_of_attacking(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.enemies.bibliotecario_errante.random.random", lambda: 0.0)
    player.stats.evasion = 0

    BibliotecarioErrante()._read_aloud(player)

    assert any(e["name"] == "confusion" for e in player.status_effects)


def test_bibliotecario_errante_bolt_deals_magical_arcane_damage(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)  # acierta y critea
    player.stats.evasion = 0
    player.stats.magic_resist = 0

    before = player.stats.health
    BibliotecarioErrante()._arcane_bolt(player)

    assert player.stats.health < before


# --- Carroñero de Cripta: vida robada ----------------------------------------------


def test_carronero_de_cripta_heals_from_a_fraction_of_the_damage_it_deals(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.99)  # acierta, sin crítico
    monkeypatch.setattr("valeterna.characters.enemies.enemy_base.random.randint", lambda a, b: 20)
    player.stats.evasion = 0
    player.stats.armor = 0

    carronero = CarroneroDeCripta()
    carronero.stats.health = 10

    carronero.perform_turn(player)

    assert carronero.stats.health > 10


# --- Guardián del Tomo Prohibido: onda de sello inevitable ------------------------


def test_guardian_del_tomo_prohibido_seal_wave_cannot_be_dodged(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.enemies.enemy_base.random.randint", lambda a, b: 15)
    player.stats.evasion = 999
    player.stats.armor = 0

    before = player.stats.health
    GuardianDelTomoProhibido()._seal_wave(player)

    assert player.stats.health < before


# --- El Archivista: guardián, autocuración y maldición ----------------------------


def test_el_archivista_is_marked_as_the_torres_guardian():
    guardian = ElArchivista()
    assert guardian.ENCOUNTER_KIND == "guardian"
    assert guardian.ENCOUNTER_LINE
    assert guardian.TAUNT_LINES


def test_el_archivista_heals_itself_below_40_percent_health():
    guardian = ElArchivista()
    guardian.stats.health = int(guardian.stats.max_health * 0.39)

    guardian._self_heal()

    assert guardian.stats.health > int(guardian.stats.max_health * 0.39)


def test_el_archivista_forbidden_bolt_can_curse_on_hit(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)  # acierta y critea
    monkeypatch.setattr("valeterna.characters.enemies.el_archivista.random.random", lambda: 0.0)  # maldice
    player.stats.evasion = 0
    player.stats.magic_resist = 0
    player.stats.armor = 6

    ElArchivista()._forbidden_bolt(player)

    assert any(e["name"] == "maldicion" for e in player.status_effects)
