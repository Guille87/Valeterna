"""Bosque de los Susurros a 10 enemigos (v0.14.0-e, GDD §4.1/§4.6-follow-up):
mecánicas propias de los 7 enemigos nuevos (tiers 4-10; Orco/Espíritu
Vengativo/Troll ya existían y no cambian). Sigue la convención del resto de
`test_*_enemies.py`: las tiradas se prueban llamando a los métodos internos
directamente en vez de a `perform_turn()` completo, para no tener que
encadenar varias tiradas de `random.random()` compartido (ver CLAUDE.md,
"Testing conventions")."""

from valeterna.characters.enemies.arana_tejesombras import AranaTejesombras
from valeterna.characters.enemies.druida_corrupto import DruidaCorrupto
from valeterna.characters.enemies.el_enraizado import ElEnraizado
from valeterna.characters.enemies.enjambre_polillas import EnjambrePolillas
from valeterna.characters.enemies.ent_corrompido import EntCorrompido
from valeterna.characters.enemies.lobo_umbrio import LoboUmbrio
from valeterna.characters.enemies.oso_espectral import OsoEspectral
from valeterna.combat.battle import ENEMY_PROGRESSION

# --- Cadena de desbloqueo -------------------------------------------------------


def test_bosque_chain_gates_the_guardian_before_the_canon():
    assert ENEMY_PROGRESSION["Troll"] == "Araña Tejesombras"
    assert ENEMY_PROGRESSION["Ent Corrompido"] == "El Enraizado"
    # El guardián abre la Ciénaga de los Ahogados (v0.14.0-f) en vez del
    # Cañón del Trueno directamente.
    assert ENEMY_PROGRESSION["El Enraizado"] == "Sanguijuela Colosal"


# --- Araña Tejesombras: mordisco con veneno --------------------------------------


def test_arana_tejesombras_can_poison_on_hit(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.enemies.arana_tejesombras.random.random", lambda: 0.0)
    player.stats.evasion = 0

    AranaTejesombras().perform_turn(player)

    assert any(e["name"] == "veneno" for e in player.status_effects)


def test_arana_tejesombras_does_not_always_poison(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)  # acierta el golpe
    monkeypatch.setattr("valeterna.characters.enemies.arana_tejesombras.random.random", lambda: 0.99)  # no envenena
    player.stats.evasion = 0

    AranaTejesombras().perform_turn(player)

    assert not any(e["name"] == "veneno" for e in player.status_effects)


# --- Druida Corrupto: autocuración, maldición y zarcillo oscuro -----------------


def test_druida_corrupto_heals_itself_below_half_health():
    druida = DruidaCorrupto()
    druida.stats.health = 10

    druida._self_heal()

    assert druida.stats.health > 10


def test_druida_corrupto_curse_reduces_armor_until_it_expires(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.enemies.druida_corrupto.random.random", lambda: 0.0)
    player.stats.armor = 6
    player.stats.evasion = 0

    DruidaCorrupto()._cast_curse(player)

    assert any(e["name"] == "maldicion" for e in player.status_effects)
    assert player.get_total_armor() == 3  # 6 - power(3)


def test_druida_corrupto_bolt_deals_magical_darkness_damage(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)  # acierta y critea
    player.stats.evasion = 0
    player.stats.magic_resist = 0

    before = player.stats.health
    DruidaCorrupto()._corrupt_bolt(player)

    assert player.stats.health < before


# --- Oso Espectral: vida robada ---------------------------------------------------


def test_oso_espectral_heals_from_a_fraction_of_the_damage_it_deals(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.99)  # acierta, sin crítico
    monkeypatch.setattr("valeterna.characters.enemies.enemy_base.random.randint", lambda a, b: 20)
    player.stats.evasion = 0
    player.stats.armor = 0

    oso = OsoEspectral()
    oso.stats.health = 10

    oso.perform_turn(player)

    assert oso.stats.health > 10  # se curó con parte de los 20 de daño infligidos


def test_oso_espectral_does_not_heal_above_its_own_max_health(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.99)
    monkeypatch.setattr("valeterna.characters.enemies.enemy_base.random.randint", lambda a, b: 20)
    player.stats.evasion = 0
    player.stats.armor = 0

    oso = OsoEspectral()

    oso.perform_turn(player)

    assert oso.stats.health == oso.stats.max_health


# --- Enjambre de Polillas Pálidas: segundo golpe y veneno ------------------------


def test_enjambre_polillas_can_add_a_second_bite(player, monkeypatch):
    """`random.random()` es una única función compartida por todo el proceso
    (ver CLAUDE.md, "Testing conventions"): un solo mock aquí también
    gobierna `resolve_hit()`. Orden real de tiradas para un turno con
    segundo golpe: acierto 1er golpe -> crítico (no) -> veneno 1er golpe (no)
    -> se suma otra polilla (sí) -> acierto 2º golpe -> veneno 2º golpe (no)."""
    monkeypatch.setattr("valeterna.characters.enemies.enemy_base.random.randint", lambda a, b: 20)
    rolls = iter([0.5, 0.5, 0.99, 0.0, 0.5, 0.99])
    monkeypatch.setattr("valeterna.characters.enemies.enjambre_polillas.random.random", lambda: next(rolls))
    player.stats.evasion = 0
    player.stats.armor = 0

    before = player.stats.health
    EnjambrePolillas().perform_turn(player)
    dealt = before - player.stats.health

    assert dealt == 30  # 20 del primer golpe + 10 (mitad) del segundo


def test_enjambre_polillas_second_bite_is_not_guaranteed(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.enemies.enemy_base.random.randint", lambda a, b: 20)
    # acierto -> sin crítico -> sin veneno -> sin segunda polilla
    rolls = iter([0.5, 0.5, 0.99, 0.99])
    monkeypatch.setattr("valeterna.characters.enemies.enjambre_polillas.random.random", lambda: next(rolls))
    player.stats.evasion = 0
    player.stats.armor = 0

    before = player.stats.health
    EnjambrePolillas().perform_turn(player)
    dealt = before - player.stats.health

    assert dealt == 20  # solo el primer golpe
    assert not any(e["name"] == "veneno" for e in player.status_effects)


# --- Lobo Umbrío: acecho tras la primera derrota ---------------------------------


def test_lobo_umbrio_ambushes_only_after_being_defeated_once(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.enemies.lobo_umbrio.random.random", lambda: 0.0)
    player.stats.evasion = 0
    lobo = LoboUmbrio()

    assert lobo.check_ambush(player, defeated_enemies=[]) is False  # nunca derrotado: sin acecho
    assert lobo.check_ambush(player, defeated_enemies=["Lobo Umbrío"]) is True
    assert lobo.check_ambush(player, defeated_enemies=["Lobo Umbrío"]) is False  # solo una vez por combate


# --- Ent Corrompido: golpe de raíces inesquivable --------------------------------


def test_ent_corrompido_root_strike_cannot_be_dodged(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.enemies.enemy_base.random.randint", lambda a, b: 15)
    player.stats.evasion = 999  # aun con evasión altísima, no hay tirada de acierto que falle
    player.stats.armor = 0

    before = player.stats.health
    EntCorrompido()._root_strike(player)

    assert player.stats.health < before


# --- El Enraizado: guardián, autocuración y maldición ----------------------------


def test_el_enraizado_is_marked_as_the_bosques_guardian():
    guardian = ElEnraizado()
    assert guardian.ENCOUNTER_KIND == "guardian"
    assert guardian.ENCOUNTER_LINE
    assert guardian.TAUNT_LINES


def test_el_enraizado_heals_itself_below_40_percent_health():
    guardian = ElEnraizado()
    guardian.stats.health = int(guardian.stats.max_health * 0.39)

    guardian._self_heal()

    assert guardian.stats.health > int(guardian.stats.max_health * 0.39)


def test_el_enraizado_dark_strike_can_curse_on_hit(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)  # acierta y critea
    monkeypatch.setattr("valeterna.characters.enemies.el_enraizado.random.random", lambda: 0.0)  # maldice
    player.stats.evasion = 0
    player.stats.magic_resist = 0
    player.stats.armor = 5

    ElEnraizado()._dark_strike(player)

    assert any(e["name"] == "maldicion" for e in player.status_effects)
