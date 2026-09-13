import pytest

from valeterna.characters.classes import CharClass, get_profile, starting_stats
from valeterna.characters.enemies.golem import GolemDePiedra
from valeterna.characters.player import Player
from valeterna.characters.stats import Stats
from valeterna.persistence.save_load import load_game, save_game


def test_get_profile_falls_back_to_vagabundo_on_unknown():
    assert get_profile("no-existe").id is CharClass.VAGABUNDO
    assert get_profile(None).id is CharClass.VAGABUNDO
    assert get_profile(CharClass.GUERRERO).id is CharClass.GUERRERO


def test_vagabundo_starting_stats_are_the_classic_character():
    s = starting_stats(CharClass.VAGABUNDO)
    assert (s.max_health, s.min_atk, s.max_atk, s.armor) == (100, 5, 10, 2)
    assert s.magic_power == 0


def test_guerrero_is_tankier_and_hits_harder():
    s = starting_stats(CharClass.GUERRERO)
    assert s.max_health == 115
    assert s.armor == 4
    assert (s.min_atk, s.max_atk) == (6, 11)


def test_picaro_is_fast_fragile_and_crit_prone():
    s = starting_stats(CharClass.PICARO)
    assert s.max_health == 90
    assert s.speed == 13
    assert s.evasion == 5
    assert s.crit_chance == pytest.approx(0.20)


def test_arcanista_trades_bulk_for_magic_power():
    s = starting_stats(CharClass.ARCANISTA)
    assert s.max_health == 85
    assert s.armor == 0
    assert s.magic_power == 8


def test_player_defaults_to_vagabundo():
    p = Player("X", Stats(100, 100, 5, 10, 2))
    assert p.char_class is CharClass.VAGABUNDO
    assert p.is_magical_attacker() is False


def test_arcanista_attack_scales_with_magic_power_not_weapon():
    p = Player("Mag", starting_stats(CharClass.ARCANISTA), char_class=CharClass.ARCANISTA)
    lo, hi = p.get_magic_attack_range()
    assert lo == 8
    assert hi >= 9
    # get_attack_damage debe salir del rango mágico, no del rango de arma (5-10 base)
    assert all(lo <= p.get_attack_damage() <= hi for _ in range(20))


def test_guerrero_armor_grows_faster_than_vagabundo():
    guer = Player("G", starting_stats(CharClass.GUERRERO), char_class=CharClass.GUERRERO)
    vaga = Player("V", starting_stats(CharClass.VAGABUNDO))
    for _ in range(9):
        guer._level_up()
        vaga._level_up()
    guer_armor_growth = guer.stats.armor - starting_stats(CharClass.GUERRERO).armor
    vaga_armor_growth = vaga.stats.armor - starting_stats(CharClass.VAGABUNDO).armor
    assert guer_armor_growth > vaga_armor_growth


def test_arcanista_magic_power_grows_on_level_up():
    p = Player("A", starting_stats(CharClass.ARCANISTA), char_class=CharClass.ARCANISTA)
    before = p.stats.magic_power
    p._level_up()
    assert p.stats.magic_power > before


def test_non_arcanista_magic_power_never_grows():
    p = Player("V", starting_stats(CharClass.VAGABUNDO))
    for _ in range(5):
        p._level_up()
    assert p.stats.magic_power == 0


def test_arcanista_attack_is_mitigated_by_magic_resist_not_armor(monkeypatch):
    """Un Gólem con 20 de armadura pero 0 de res. mágica encaja casi todo el
    golpe mágico del Arcanista (la armadura no lo frena)."""
    monkeypatch.setattr("random.random", lambda: 0.99)  # sin crítico
    from valeterna.combat import battle

    p = Player("A", starting_stats(CharClass.ARCANISTA), char_class=CharClass.ARCANISTA)
    p.stats.magic_power = 40
    golem = GolemDePiedra()
    golem.stats.magic_resist = 0
    hp_before = golem.stats.health
    monkeypatch.setattr(p, "get_attack_damage", lambda: 40)
    monkeypatch.setattr("valeterna.combat.battle.resolve_hit", lambda *a, **k: True)
    battle._execute_turn(p, golem, [])
    # armadura 20 ignorada -> el golpe entra casi entero (>30 de 40)
    assert hp_before - golem.stats.health >= 30


def test_save_load_round_trips_class_and_equipped_skills(tmp_save_dir):
    p = Player("Guille", starting_stats(CharClass.ARCANISTA), char_class=CharClass.ARCANISTA)
    p.equipped_skills = ["proyectil_arcano"]
    save_game(p, unlocked_enemies=["Goblin"], defeated_enemies=[])

    loaded = Player("Guille", Stats(1, 1, 1, 1, 1))
    load_game(loaded)
    assert loaded.char_class is CharClass.ARCANISTA
    assert loaded.equipped_skills == ["proyectil_arcano"]
    assert loaded.stats.magic_power == p.stats.magic_power


def test_legacy_save_without_class_loads_as_vagabundo(tmp_save_dir):
    p = Player("Legacy", Stats(100, 100, 5, 10, 2))
    save_game(p, unlocked_enemies=["Goblin"], defeated_enemies=[])
    # Reescribe el .sav sin las claves nuevas.
    import base64
    import json

    path = tmp_save_dir / "Legacy.sav"
    data = json.loads(base64.b64decode(path.read_bytes()).decode())
    data.pop("clase", None)
    data.pop("habilidades_equipadas", None)
    data["player_stats"].pop("magic_power", None)
    path.write_bytes(base64.b64encode(json.dumps(data).encode()))

    loaded = Player("Legacy", Stats(1, 1, 1, 1, 1))
    load_game(loaded)
    assert loaded.char_class is CharClass.VAGABUNDO
    # Sin habilidades guardadas, al cargar se auto-equipan las activas conocidas.
    assert loaded.equipped_skills == ["golpe_firme"]
    assert loaded.stats.magic_power == 0
