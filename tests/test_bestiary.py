"""Bestiario progresivo (GDD §7.2, v0.14.0-a): la ficha se revela por escalones
según las veces que se ha derrotado al enemigo, y la tabla de drops se deduce del
propio `drop_item()`."""

import random

import pytest

from valeterna import i18n
from valeterna.characters.enemies.dragon import Dragon
from valeterna.characters.enemies.goblin import Goblin
from valeterna.characters.enemies.mage import Mago
from valeterna.characters.enemies.skeleton import Skeleton
from valeterna.combat.battle import ENEMY_PROGRESSION
from valeterna.combat.elements import ELEMENTS
from valeterna.ui.formatting import print_bestiary_entry
from valeterna.ui.menus import _get_enemy_instance


def _sheet(enemy, kills, capsys):
    print_bestiary_entry(enemy, kill_count=kills)
    return capsys.readouterr().out


# --- Escalones ----------------------------------------------------------------


def test_first_kill_shows_only_the_basics(capsys):
    out = _sheet(Goblin(), 1, capsys)

    assert "Veces derrotado: 1" in out
    assert Goblin.DESCRIPTION in out
    assert "Vida máxima" in out and "Ataque:" in out and "Oro al derrotarlo" in out
    for hidden in ("Armadura", "Velocidad", "Habilidad:", "Débil a", "Botín posible"):
        assert hidden not in out
    assert "Derrótalo 3 veces" in out


def test_three_kills_add_combat_stats_and_the_signature(capsys):
    out = _sheet(Goblin(), 3, capsys)

    assert "Armadura" in out and "Velocidad" in out and "Prob. Crítico" in out
    assert f"Habilidad: {Goblin.SIGNATURE}" in out
    assert "Derrótalo 5 veces" in out
    assert "Resiste:" not in out and "Botín posible" not in out


def test_five_kills_add_affinities_and_statuses(capsys):
    out = _sheet(Skeleton(), 5, capsys)

    assert "Débil a" in out and "Resiste:" in out
    assert "Inmune a los estados" in out
    assert "Derrótalo 10 veces" in out
    assert "Botín posible" not in out


def test_five_kills_show_the_statuses_it_can_inflict(capsys):
    out = _sheet(Mago(), 5, capsys)

    assert "Puede infligirte" in out
    for word in ("quemadura", "parálisis", "veneno", "congelación"):
        assert word in out


def test_ten_kills_reveal_the_drop_table_and_no_more_hints(capsys):
    out = _sheet(Goblin(), 10, capsys)

    assert "Botín posible" in out
    assert "Espada Goblin (arma): 10%" in out
    assert "Poción de Salud (poción): 80%" in out
    assert "Colmillo de Goblin (material de herrería): 25%" in out
    assert "Derrótalo" not in out


def test_the_element_its_attacks_deal_shows_from_the_first_kill(capsys):
    assert "Sus ataques infligen" in _sheet(Dragon(), 1, capsys)
    assert "Sus ataques infligen" not in _sheet(Goblin(), 1, capsys)
    out = _sheet(Mago(), 1, capsys)
    for element in ("Fuego", "Rayo", "Veneno", "Hielo"):
        assert element in out


def test_lore_line_is_not_tinted_by_status_words(monkeypatch, capsys):
    from colorama import Fore

    monkeypatch.setattr(Dragon, "DESCRIPTION", "Un bando quemado y un veneno cualquiera.")
    out = _sheet(Dragon(), 1, capsys)

    assert "bando quemado" in out
    assert Fore.RED + "quemado" not in out


# --- Tabla de drops -----------------------------------------------------------


def test_drop_table_pairs_each_item_with_its_probability():
    table = Goblin().drop_table()

    assert [(item.name, chance) for item, chance in table] == [
        ("Espada Goblin", 0.1),
        ("Poción de Salud", 0.8),
        ("Colmillo de Goblin", 0.25),
    ]


def test_drop_table_leaves_random_untouched_and_drops_nothing_for_real():
    original = random.random

    Goblin().drop_table()

    assert random.random is original


def test_drop_table_stays_consistent_with_drop_item_for_the_whole_roster(monkeypatch):
    """Forzando todas las tiradas a acertar, `drop_item()` suelta exactamente los
    objetos de `drop_table()` — así la tabla del Bestiario no puede desincronizarse."""
    for name in ENEMY_PROGRESSION:
        enemy = _get_enemy_instance(name)
        table = enemy.drop_table()
        with monkeypatch.context() as m:
            m.setattr(random, "random", lambda: 0.0)
            real = enemy.drop_item()
        assert [i.name for i, _ in table] == [i.name for i in real], name
        assert all(0 < chance <= 1 for _, chance in table), name


# --- Fichas completas de todo el roster ---------------------------------------


@pytest.mark.parametrize("name", list(ENEMY_PROGRESSION))
def test_every_enemy_has_a_complete_sheet(name):
    cls = type(_get_enemy_instance(name))

    assert cls.DESCRIPTION.strip(), name
    assert cls.SIGNATURE.strip(), name
    assert set(ELEMENTS) >= cls.ELEMENTS_DEALT, name
    for status in cls.INFLICTS | cls.IMMUNE_STATUSES:
        assert i18n.has(f"status.{status}"), f"{name}: falta el nombre legible de {status!r}"


@pytest.mark.parametrize("name", list(ENEMY_PROGRESSION))
def test_every_enemys_full_sheet_renders_without_errors(name, capsys):
    print_bestiary_entry(_get_enemy_instance(name), kill_count=10)

    assert name in capsys.readouterr().out
