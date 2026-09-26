"""Tests de las mecánicas propias de los enemigos originales (Goblin, Esqueleto,
Orco, Mago), que hasta ahora solo se ejercitaban de refilón desde test_battle.

`random.random` / `randint` / `choice` son funciones del módulo stdlib compartido
por todo el proceso: parchearlas afecta a cualquier llamada (stats.resolve_hit
incluida), así que los tests fijan valores extremos y comprueban efectos, no
números exactos de daño.
"""

import pytest

from valeterna.characters.enemies.goblin import Goblin
from valeterna.characters.enemies.mage import Mago
from valeterna.characters.enemies.orc import Orc
from valeterna.characters.enemies.skeleton import Skeleton


@pytest.fixture
def always_low(monkeypatch):
    """Todas las tiradas salen 0.0: los golpes aciertan y los efectos se aplican."""
    monkeypatch.setattr("random.random", lambda: 0.0)
    monkeypatch.setattr("random.randint", lambda a, b: 10)


@pytest.fixture
def always_high(monkeypatch):
    monkeypatch.setattr("random.random", lambda: 0.99)
    monkeypatch.setattr("random.randint", lambda a, b: 10)


# --- Goblin: emboscada previa al combate ---


def test_goblin_ambush_hits_once_then_never_again(player, always_low):
    player.stats.armor = 0
    goblin = Goblin()
    before = player.stats.health

    assert goblin.check_ambush(player, ["Goblin"]) is True
    assert player.stats.health < before
    assert goblin.check_ambush(player, ["Goblin"]) is False  # ambush_done ya está marcado


def test_goblin_ambush_can_fail(player, always_high):
    assert Goblin().check_ambush(player, ["Goblin"]) is False


def test_goblin_never_ambushes_until_it_has_been_defeated_once(player, always_low):
    player.stats.armor = 0
    before = player.stats.health

    assert Goblin().check_ambush(player, []) is False
    assert Goblin().check_ambush(player, None) is False
    assert Goblin().check_ambush(player, ["Huargo"]) is False
    assert player.stats.health == before


# --- Esqueleto: reanimación ---


def test_skeleton_revives_once_at_zero_health():
    skel = Skeleton()
    skel.take_damage(500)

    assert skel.has_revived
    assert skel.stats.health == skel.stats.max_health // 2
    assert skel.is_alive()


def test_skeleton_dies_on_the_second_lethal_hit():
    skel = Skeleton()
    skel.take_damage(500)
    skel.take_damage(500)

    assert not skel.is_alive()


def test_skeleton_revive_shows_hp_only_when_in_bestiary(capsys):
    Skeleton().take_damage(500, defeated_enemies=["Esqueleto"])
    assert "ha revivido con 56 HP" in capsys.readouterr().out

    Skeleton().take_damage(500, defeated_enemies=[])
    assert "??? HP" in capsys.readouterr().out


# --- Orco: ciclo de furia ---


def test_orc_fury_cycle_toggles_every_three_turns():
    orc = Orc()
    for _ in range(3):
        orc.on_turn_end()
    assert orc.fury_active
    for _ in range(3):
        orc.on_turn_end()
    assert not orc.fury_active


def test_orc_enrage_message_is_deferred_to_an_announcement():
    orc = Orc()
    for _ in range(2):
        orc.on_turn_end()
    assert orc.pop_announcements() == []  # todavía no

    orc.on_turn_end()  # 3er turno -> se enfurece
    msgs = orc.pop_announcements()
    assert len(msgs) == 1 and "enfurecido" in msgs[0]
    assert orc.pop_announcements() == []  # ya consumido


def test_orc_fury_attack_doubles_post_mitigation_damage(player, monkeypatch):
    monkeypatch.setattr("random.random", lambda: 0.99)  # sin crítico, pero acierta contra evasión 0
    monkeypatch.setattr("random.randint", lambda a, b: 18)
    player.stats.armor = 0
    player.stats.evasion = 0

    orc = Orc()
    orc.fury_active = True
    before = player.stats.health
    orc.perform_turn(player)

    assert before - player.stats.health == 36  # 18 de base, sin mitigación, x2


def test_orc_fury_attack_can_miss(player, monkeypatch):
    monkeypatch.setattr("random.random", lambda: 0.99)
    player.stats.evasion = 500

    orc = Orc()
    orc.fury_active = True
    before = player.stats.health
    orc.perform_turn(player)

    assert player.stats.health == before


# --- Mago: curación y hechizos ---


def test_mago_self_heals_when_below_half_health(player, monkeypatch):
    monkeypatch.setattr("random.random", lambda: 0.0)  # 0.0 < 0.4 -> cura
    monkeypatch.setattr("random.randint", lambda a, b: 50)

    mago = Mago()
    mago.stats.health = 100  # <= 200 (50% de 400)
    mago.perform_turn(player)

    assert mago.stats.health == 150


def test_mago_casts_a_spell_and_damages_the_player_when_healthy(player, always_low):
    player.stats.evasion = 0
    mago = Mago()
    before = player.stats.health
    mago.perform_turn(player)

    assert player.stats.health < before


@pytest.mark.parametrize("spell", ["thunder", "poison", "blizzard"])
def test_mago_perform_turn_dispatches_the_chosen_spell(player, monkeypatch, spell):
    # random.random() = 0.35: vida alta -> no cura, y 0.35 >= 0.3 -> no bola de
    # fuego, así que entra en random.choice(); forzamos el hechizo y comprobamos
    # que hace daño (prueba de que se ha despachado).
    monkeypatch.setattr("random.random", lambda: 0.35)
    monkeypatch.setattr("random.randint", lambda a, b: 10)
    monkeypatch.setattr("random.choice", lambda opts: spell)
    player.stats.evasion = 0

    before = player.stats.health
    Mago().perform_turn(player)
    assert player.stats.health < before


@pytest.mark.parametrize("method", ["_cast_thunder", "_cast_poison", "_cast_blizzard"])
def test_mago_spells_can_miss(player, monkeypatch, method):
    monkeypatch.setattr("random.random", lambda: 0.99)
    monkeypatch.setattr("random.randint", lambda a, b: 10)
    player.stats.evasion = 500

    mago = Mago()
    before = player.stats.health
    getattr(mago, method)(player)
    assert player.stats.health == before


def test_mago_fireball_can_be_dodged(player, monkeypatch):
    monkeypatch.setattr("random.random", lambda: 0.99)
    player.stats.evasion = 500

    mago = Mago()
    before = player.stats.health
    mago._cast_fireball(player)

    assert player.stats.health == before


@pytest.mark.parametrize(
    ("method", "status"),
    [
        ("_cast_fireball", "quemado"),
        ("_cast_thunder", "paralizado"),
        ("_cast_poison", "veneno"),
        ("_cast_blizzard", "congelado"),
    ],
)
def test_mago_spells_apply_their_status_on_a_clean_hit(player, always_low, method, status):
    player.stats.evasion = 0
    mago = Mago()
    before = player.stats.health

    getattr(mago, method)(player)

    assert player.stats.health < before
    assert any(e["name"] == status for e in player.status_effects)


# --- drop_item de cada enemigo (devuelve lista) ---


@pytest.mark.parametrize(
    ("enemy_cls", "expected"),
    [
        (Goblin, {"Espada Goblin"}),
        (Skeleton, {"Casco de Hueso", "Poción de Salud", "Fragmento de Hueso", "Guantes Óseos"}),
        (Mago, {"Bastón Arcano", "Túnica Arcana", "Esencia Arcana", "Anillo Arcano"}),
    ],
)
def test_drop_item_returns_every_possible_item_when_lucky(monkeypatch, enemy_cls, expected):
    monkeypatch.setattr("random.random", lambda: 0.0)
    drops = enemy_cls().drop_item()
    names = drops.name if not isinstance(drops, list) else {i.name for i in drops}
    assert expected <= names
