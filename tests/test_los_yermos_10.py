"""Los Yermos a 10 enemigos (v0.14.0-c, GDD §4.6): mecánicas propias de los 6
enemigos nuevos. Sigue la convención del resto de `test_*_enemies.py`: las
tiradas se prueban llamando a los métodos internos directamente en vez de a
`perform_turn()` completo, para no tener que encadenar varias tiradas de
`random.random()` compartido (ver CLAUDE.md, "Testing conventions")."""

from valeterna.characters.enemies.chaman_goblin import ChamanGoblin
from valeterna.characters.enemies.el_carnicero import ElCarnicero
from valeterna.characters.enemies.goblin_montaraz import GoblinMontaraz
from valeterna.characters.enemies.ogro_del_yermo import OgroDelYermo
from valeterna.characters.enemies.rata_gigante import RataGigante
from valeterna.characters.enemies.salteador import Salteador
from valeterna.combat.battle import ENEMY_PROGRESSION

# --- Cadena de desbloqueo -------------------------------------------------------


def test_los_yermos_chain_gates_the_guardian_before_the_bosque():
    assert ENEMY_PROGRESSION["Goblin"] == "Rata Gigante"
    assert ENEMY_PROGRESSION["Ogro del Yermo"] == "El Carnicero"
    assert ENEMY_PROGRESSION["El Carnicero"] == "Orco"  # el guardián abre el Bosque


# --- Rata Gigante: mordisco con veneno ------------------------------------------


def test_rata_gigante_can_poison_on_hit(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.enemies.rata_gigante.random.random", lambda: 0.0)
    player.stats.evasion = 0

    RataGigante().perform_turn(player)

    assert any(e["name"] == "veneno" for e in player.status_effects)


def test_rata_gigante_does_not_always_poison(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)  # acierta el golpe
    monkeypatch.setattr("valeterna.characters.enemies.rata_gigante.random.random", lambda: 0.99)  # no envenena
    player.stats.evasion = 0

    RataGigante().perform_turn(player)

    assert not any(e["name"] == "veneno" for e in player.status_effects)


# --- Goblin Montaraz: sin trato especial a la evasión ---------------------------


def test_goblin_montaraz_can_still_be_dodged_like_any_other_attack(player, monkeypatch):
    """El ataque a distancia usa la misma tirada de acierto que cualquier otro
    (feedback del usuario: nada de ignorar evasión "porque es una flecha")."""
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.99)  # falla siempre
    player.stats.evasion = 999

    before = player.stats.health
    GoblinMontaraz().perform_turn(player)

    assert player.stats.health == before


def test_goblin_montaraz_can_cause_bleed_on_hit(player, monkeypatch):
    rolls = iter([0.0, 0.99, 0.0])  # acierta, sin crítico, sangra
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: next(rolls))
    player.stats.evasion = 0

    GoblinMontaraz().perform_turn(player)

    assert any(e["name"] == "sangrado" for e in player.status_effects)


# --- Chamán Goblin: autocuración, maldición y dardo oscuro ----------------------


def test_chaman_goblin_heals_itself_below_half_health():
    chaman = ChamanGoblin()
    chaman.stats.health = 10

    chaman._self_heal()

    assert chaman.stats.health > 10


def test_chaman_goblin_curse_reduces_armor_until_it_expires(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.enemies.chaman_goblin.random.random", lambda: 0.0)
    player.stats.armor = 5
    player.stats.evasion = 0

    ChamanGoblin()._cast_curse(player)

    assert any(e["name"] == "maldicion" for e in player.status_effects)
    assert player.get_total_armor() == 3  # 5 - power(2)


def test_chaman_goblin_dark_bolt_deals_magical_darkness_damage(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)  # acierta y critea
    player.stats.evasion = 0
    player.stats.magic_resist = 0

    before = player.stats.health
    ChamanGoblin()._dark_bolt(player)

    assert player.stats.health < before


# --- Salteador: doble golpe y robo de oro controlado ----------------------------


def test_salteador_second_strike_adds_bonus_damage(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)
    player.stats.evasion = 0
    player.stats.armor = 0

    before = player.stats.health
    Salteador()._second_strike(player)

    assert player.stats.health < before


def test_salteador_steal_never_takes_more_gold_than_the_player_has(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.enemies.salteador.random.random", lambda: 0.0)  # acierta siempre
    monkeypatch.setattr("valeterna.characters.enemies.salteador.random.randint", lambda a, b: 999)
    player.stats.evasion = 0
    player.inventory.gold = 5

    Salteador()._steal(player)

    assert player.inventory.gold == 0  # nunca negativo, nunca más de lo que llevaba


def test_salteador_steal_does_nothing_but_taunt_when_player_has_no_gold(player, monkeypatch, capsys):
    monkeypatch.setattr("valeterna.characters.enemies.salteador.random.random", lambda: 0.0)
    player.stats.evasion = 0
    player.inventory.gold = 0

    Salteador()._steal(player)

    assert player.inventory.gold == 0
    assert "no lleva nada" in capsys.readouterr().out


def test_salteador_steal_can_be_dodged(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.enemies.salteador.random.random", lambda: 0.99)
    player.stats.evasion = 999
    player.inventory.gold = 20

    Salteador()._steal(player)

    assert player.inventory.gold == 20


# --- Ogro del Yermo: golpe aplastante con aturdimiento --------------------------


def test_ogro_del_yermo_crushing_blow_deals_more_than_a_normal_hit(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.99)  # acierta, sin crítico
    monkeypatch.setattr("valeterna.characters.enemies.enemy_base.random.randint", lambda a, b: 10)
    player.stats.evasion = 0
    player.stats.armor = 0

    before = player.stats.health
    OgroDelYermo()._crushing_blow(player)
    dealt = before - player.stats.health

    assert dealt == int(10 * 1.6)


def test_ogro_del_yermo_crushing_blow_can_stun(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)  # acierta
    monkeypatch.setattr("valeterna.characters.enemies.ogro_del_yermo.random.random", lambda: 0.0)  # aturde
    player.stats.evasion = 0

    OgroDelYermo()._crushing_blow(player)

    assert any(e["name"] == "aturdido" for e in player.status_effects)


# --- El Carnicero: furia de un solo sentido -------------------------------------


def test_el_carnicero_enrages_once_below_40_percent_health():
    carnicero = ElCarnicero()
    carnicero.stats.health = int(carnicero.stats.max_health * 0.5)

    carnicero.on_turn_end()
    assert carnicero.enraged is False

    carnicero.stats.health = int(carnicero.stats.max_health * 0.39)
    carnicero.on_turn_end()

    assert carnicero.enraged is True
    assert "furia" in " ".join(carnicero.pop_announcements()).lower()


def test_el_carnicero_enrage_does_not_turn_off_if_health_recovers():
    carnicero = ElCarnicero()
    carnicero.stats.health = 1
    carnicero.on_turn_end()
    assert carnicero.enraged is True

    carnicero.stats.health = carnicero.stats.max_health
    carnicero.on_turn_end()

    assert carnicero.enraged is True  # de un solo sentido, no cíclica como el Orco


def test_el_carnicero_hits_harder_while_enraged(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.99)  # acierta, sin crítico
    monkeypatch.setattr("valeterna.characters.enemies.enemy_base.random.randint", lambda a, b: 10)
    player.stats.evasion = 0
    player.stats.armor = 0

    carnicero = ElCarnicero()
    carnicero.enraged = True

    before = player.stats.health
    carnicero.perform_turn(player)
    dealt = before - player.stats.health

    assert dealt == int(10 * 1.4)
