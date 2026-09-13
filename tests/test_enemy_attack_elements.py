"""Los ataques elementales de los enemigos etiquetan su elemento al golpear al
jugador (v0.11.0-b), para que Player.get_total_resist() pueda aplicarse.
Antes de esto, take_damage() solo distinguía is_fire/is_magical, sin ningún
elemento genérico."""

from valeterna.characters.enemies.angel_caido import AngelCaido
from valeterna.characters.enemies.demonio import Demonio
from valeterna.characters.enemies.dragon import Dragon
from valeterna.characters.enemies.mage import Mago
from valeterna.characters.enemies.nigromante import Nigromante


def _spy_take_damage(player, monkeypatch):
    calls = {}
    original = player.take_damage
    monkeypatch.setattr(player, "take_damage", lambda amount, **kw: (calls.update(kw), original(amount, **kw))[1])
    return calls


def test_mage_fireball_tags_fuego(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)  # acierta, sin crítico ni quemadura
    monkeypatch.setattr("valeterna.characters.enemies.mage.random.randint", lambda a, b: 10)
    monkeypatch.setattr("valeterna.characters.enemies.mage.random.random", lambda: 0.99)
    calls = _spy_take_damage(player, monkeypatch)

    Mago()._cast_fireball(player)

    assert calls.get("element") == "fuego"


def test_mage_thunder_tags_rayo(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)
    monkeypatch.setattr("valeterna.characters.enemies.mage.random.randint", lambda a, b: 10)
    monkeypatch.setattr("valeterna.characters.enemies.mage.random.random", lambda: 0.99)
    calls = _spy_take_damage(player, monkeypatch)

    Mago()._cast_thunder(player)

    assert calls.get("element") == "rayo"


def test_mage_poison_tags_veneno(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)
    monkeypatch.setattr("valeterna.characters.enemies.mage.random.randint", lambda a, b: 10)
    monkeypatch.setattr("valeterna.characters.enemies.mage.random.random", lambda: 0.99)
    calls = _spy_take_damage(player, monkeypatch)

    Mago()._cast_poison(player)

    assert calls.get("element") == "veneno"


def test_mage_blizzard_tags_hielo(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)
    monkeypatch.setattr("valeterna.characters.enemies.mage.random.randint", lambda a, b: 10)
    monkeypatch.setattr("valeterna.characters.enemies.mage.random.random", lambda: 0.99)
    calls = _spy_take_damage(player, monkeypatch)

    Mago()._cast_blizzard(player)

    assert calls.get("element") == "hielo"


def test_nigromante_dark_bolt_tags_oscuridad(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)
    monkeypatch.setattr("valeterna.characters.enemies.enemy_base.random.randint", lambda a, b: 10)
    calls = _spy_take_damage(player, monkeypatch)

    Nigromante()._dark_bolt(player)

    assert calls.get("element") == "oscuridad"


def test_angel_caido_holy_strike_tags_sagrado(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)
    monkeypatch.setattr("valeterna.characters.enemies.enemy_base.random.randint", lambda a, b: 10)
    calls = _spy_take_damage(player, monkeypatch)

    AngelCaido()._holy_strike(player)

    assert calls.get("element") == "sagrado"


def test_angel_caido_divine_judgment_tags_sagrado(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)
    monkeypatch.setattr("valeterna.characters.enemies.enemy_base.random.randint", lambda a, b: 10)
    calls = _spy_take_damage(player, monkeypatch)

    AngelCaido()._divine_judgment(player)

    assert calls.get("element") == "sagrado"


def test_dragon_fire_breath_tags_fuego(player, monkeypatch):
    # Secuencia: [¿acierta?, ¿quema?]
    rolls = iter([0.0, 0.99])
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: next(rolls))
    monkeypatch.setattr("valeterna.characters.enemies.enemy_base.random.randint", lambda a, b: 10)
    calls = _spy_take_damage(player, monkeypatch)

    Dragon()._fire_breath(player)

    assert calls.get("element") == "fuego"


def test_demonio_claw_attack_tags_fuego(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)
    monkeypatch.setattr("valeterna.characters.enemies.enemy_base.random.randint", lambda a, b: 10)
    calls = _spy_take_damage(player, monkeypatch)

    Demonio()._claw_attack(player)

    assert calls.get("element") == "fuego"


def test_demonio_summon_lesser_demon_tags_fuego(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)
    monkeypatch.setattr("valeterna.characters.enemies.enemy_base.random.randint", lambda a, b: 10)
    calls = _spy_take_damage(player, monkeypatch)

    Demonio()._summon_lesser_demon(player)

    assert calls.get("element") == "fuego"
