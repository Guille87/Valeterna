from valeterna import updater
from valeterna.ui import menus


def _info(tag="v0.4.0"):
    return updater.UpdateInfo(version=tag.lstrip("v"), tag=tag, zip_url="https://x/z.zip", sha256=None, notes="")


def test_update_notice_prints_every_time_an_update_is_available(monkeypatch, capsys):
    """A propósito NO se limita a una vez: debe salir en cada redibujado del
    menú y al entrar a nueva/cargar partida, por si el jugador va rápido."""
    monkeypatch.setattr(menus.updater, "available", lambda: _info("v0.5.0"))

    menus._maybe_show_update_notice(in_game=False)
    first = capsys.readouterr().out
    menus._maybe_show_update_notice(in_game=False)
    second = capsys.readouterr().out

    assert "v0.5.0" in first
    assert "v0.5.0" in second


def test_update_notice_in_game_points_to_the_main_menu(monkeypatch, capsys):
    monkeypatch.setattr(menus.updater, "available", lambda: _info())
    menus._maybe_show_update_notice(in_game=True)
    assert "Menú Principal" in capsys.readouterr().out


def test_no_update_notice_when_nothing_is_available(monkeypatch, capsys):
    monkeypatch.setattr(menus.updater, "available", lambda: None)
    menus._maybe_show_update_notice(in_game=False)
    assert capsys.readouterr().out == ""


def test_load_saved_game_shows_the_update_notice_before_asking(monkeypatch, capsys):
    monkeypatch.setattr(menus.updater, "available", lambda: _info("v0.5.0"))
    monkeypatch.setattr(menus.console, "ask", lambda _="": "Nadie")
    monkeypatch.setattr(menus, "load_game", lambda _p: None)

    menus.load_saved_game()

    assert "v0.5.0" in capsys.readouterr().out


def test_check_updates_now_reports_a_new_version(monkeypatch, capsys):
    monkeypatch.setattr(menus.updater, "check", lambda: _info("v9.0.0"))
    menus._check_updates_now()
    assert "v9.0.0" in capsys.readouterr().out


def test_check_updates_now_reports_up_to_date(monkeypatch, capsys):
    monkeypatch.setattr(menus.updater, "check", lambda: None)
    monkeypatch.setattr(menus.updater, "_current_version", lambda: "0.3.0")
    menus._check_updates_now()
    assert "0.3.0" in capsys.readouterr().out
