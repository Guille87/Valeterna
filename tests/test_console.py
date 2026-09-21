"""Tests de la capa de presentación: coloreado de estados y de estadísticas."""

import pytest
from colorama import Fore

from valeterna.ui import console


def test_tint_status_colors_each_state_keyword():
    out = console.tint_status("veneno quemadura parálisis congelación")
    assert Fore.GREEN in out  # veneno
    assert Fore.RED in out  # quemadura
    assert Fore.YELLOW in out  # parálisis
    assert Fore.BLUE in out  # congelación


def test_tint_status_is_case_insensitive_and_matches_word_forms():
    assert Fore.GREEN in console.tint_status("Estás envenenado")
    assert Fore.RED in console.tint_status("Te has QUEMADO")
    assert Fore.BLUE in console.tint_status("El enemigo te deja congelado")


def test_tint_status_leaves_unrelated_text_untouched():
    assert console.tint_status("un texto normal sin estados") == "un texto normal sin estados"


def test_colorize_auto_tints_state_keywords_inside_a_colored_line():
    out = console.colorize("El veneno te quita 5 HP", Fore.RED)
    assert Fore.GREEN in out  # la palabra "veneno" va en verde aunque la línea sea roja


def test_say_prints_the_line_with_states_tinted(capsys):
    console.say("El veneno recorre tus venas")
    out = capsys.readouterr().out
    assert "recorre tus venas" in out
    assert Fore.GREEN in out


def test_ask_exits_cleanly_when_stdin_is_closed(monkeypatch):
    def _eof(_prompt):
        raise EOFError

    monkeypatch.setattr("builtins.input", _eof)
    with pytest.raises(SystemExit) as exc:
        console.ask("nombre: ")
    assert exc.value.code == 0


def test_stat_line_uses_the_color_for_that_concept():
    assert console.STAT_COLORS["vida"] in console.stat_line("Vida: 10/10", "vida")
    # Un concepto desconocido no revienta, cae a blanco
    assert console.stat_line("Algo: 1", "no_existe")


def test_colorize_can_skip_status_tinting():
    assert Fore.RED in console.colorize("Bando quemado", Fore.YELLOW)
    assert Fore.RED not in console.colorize("Bando quemado", Fore.YELLOW, tint=False)
