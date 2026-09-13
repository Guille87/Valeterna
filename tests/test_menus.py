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


def test_check_admin_password_returns_false_without_a_configured_hash(monkeypatch):
    monkeypatch.setattr(menus, "_ADMIN_PASSWORD_HASH", "")
    assert menus._check_admin_password() is False


def test_check_admin_password_uses_getpass_on_a_real_terminal(monkeypatch):
    monkeypatch.setattr(menus, "_ADMIN_PASSWORD_HASH", menus.hashlib.sha256(b"secreto").hexdigest())
    monkeypatch.setattr(menus.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(menus.getpass, "getpass", lambda _prompt: "secreto")
    monkeypatch.setattr(
        menus.console, "ask", lambda _prompt: (_ for _ in ()).throw(AssertionError("no debería usarse"))
    )

    assert menus._check_admin_password() is True


def test_check_admin_password_falls_back_to_getpass_exceptions(monkeypatch):
    monkeypatch.setattr(menus, "_ADMIN_PASSWORD_HASH", menus.hashlib.sha256(b"secreto").hexdigest())
    monkeypatch.setattr(menus.sys.stdin, "isatty", lambda: True)

    def _boom(_prompt):
        raise RuntimeError("getpass no soportado")

    monkeypatch.setattr(menus.getpass, "getpass", _boom)
    monkeypatch.setattr(menus.console, "ask", lambda _prompt: "secreto")

    assert menus._check_admin_password() is True


def test_check_admin_password_skips_getpass_without_a_real_terminal(monkeypatch):
    # Sin terminal real (p. ej. el panel "Run" de PyCharm), `getpass` puede
    # quedarse colgado sin lanzar excepción, así que ni se intenta.
    monkeypatch.setattr(menus, "_ADMIN_PASSWORD_HASH", menus.hashlib.sha256(b"secreto").hexdigest())
    monkeypatch.setattr(menus.sys.stdin, "isatty", lambda: False)
    monkeypatch.setattr(
        menus.getpass, "getpass", lambda _prompt: (_ for _ in ()).throw(AssertionError("no debería llamarse"))
    )
    monkeypatch.setattr(menus.console, "ask", lambda _prompt: "secreto")

    assert menus._check_admin_password() is True


def test_check_admin_password_rejects_a_wrong_password(monkeypatch):
    monkeypatch.setattr(menus, "_ADMIN_PASSWORD_HASH", menus.hashlib.sha256(b"secreto").hexdigest())
    monkeypatch.setattr(menus.sys.stdin, "isatty", lambda: False)
    monkeypatch.setattr(menus.console, "ask", lambda _prompt: "incorrecta")

    assert menus._check_admin_password() is False
