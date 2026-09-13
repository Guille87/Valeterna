import sys
import threading

from valeterna.config import logging_setup


def test_report_crash_writes_a_crash_file_with_traceback(tmp_path, monkeypatch):
    monkeypatch.setattr(logging_setup, "LOG_DIR", tmp_path)
    monkeypatch.setattr(logging_setup, "LOG_FILE", tmp_path / "juego.log")

    try:
        raise ValueError("objeto raro sin get_stats_info")
    except ValueError as exc:
        crash_path = logging_setup.report_crash(exc, context="test inventario")

    assert crash_path is not None
    assert crash_path.exists()
    contents = crash_path.read_text(encoding="utf-8")
    assert "ValueError: objeto raro sin get_stats_info" in contents
    assert "Traceback" in contents
    assert "test inventario" in contents


def test_setup_logging_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setattr(logging_setup, "LOG_DIR", tmp_path)
    monkeypatch.setattr(logging_setup, "LOG_FILE", tmp_path / "juego.log")
    monkeypatch.setattr(logging_setup, "_configured", False)
    monkeypatch.setattr(logging_setup.logger, "handlers", [])
    # setup_logging instala hooks globales; los restauramos al acabar el test.
    monkeypatch.setattr(sys, "excepthook", sys.excepthook)
    monkeypatch.setattr(threading, "excepthook", threading.excepthook)

    logging_setup.setup_logging()
    logging_setup.setup_logging()

    assert len(logging_setup.logger.handlers) == 1


def test_log_session_end_is_a_noop_when_not_configured(monkeypatch):
    """No debe lanzar aunque setup_logging() no se haya llamado."""
    monkeypatch.setattr(logging_setup, "_configured", False)
    logging_setup.log_session_end()  # sin excepción


def test_handle_uncaught_writes_a_crash_file(tmp_path, monkeypatch):
    monkeypatch.setattr(logging_setup, "LOG_DIR", tmp_path)
    monkeypatch.setattr(logging_setup, "LOG_FILE", tmp_path / "juego.log")
    monkeypatch.setattr(sys, "__excepthook__", lambda *a: None)

    exc = RuntimeError("algo se rompió")
    logging_setup._handle_uncaught(RuntimeError, exc, exc.__traceback__)

    assert list(tmp_path.glob("crash_*.txt"))


def test_handle_uncaught_ignores_keyboard_interrupt(tmp_path, monkeypatch):
    monkeypatch.setattr(logging_setup, "LOG_DIR", tmp_path)
    monkeypatch.setattr(logging_setup, "LOG_FILE", tmp_path / "juego.log")
    monkeypatch.setattr(sys, "__excepthook__", lambda *a: None)

    logging_setup._handle_uncaught(KeyboardInterrupt, KeyboardInterrupt(), None)

    assert not list(tmp_path.glob("crash_*.txt"))


def test_report_crash_returns_none_when_the_dir_cannot_be_written(tmp_path, monkeypatch):
    monkeypatch.setattr(logging_setup, "LOG_DIR", tmp_path / "no")
    monkeypatch.setattr(logging_setup, "LOG_FILE", tmp_path / "no" / "juego.log")

    def boom(*a, **k):
        raise OSError("sin permiso")

    monkeypatch.setattr(logging_setup.Path, "mkdir", boom)
    assert logging_setup.report_crash(ValueError("x"), context="t") is None


def test_setup_logging_survives_a_dir_creation_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(logging_setup, "LOG_DIR", tmp_path / "no")
    monkeypatch.setattr(logging_setup, "_configured", False)
    monkeypatch.setattr(logging_setup.logger, "handlers", [])
    monkeypatch.setattr(logging_setup.Path, "mkdir", lambda *a, **k: (_ for _ in ()).throw(OSError()))

    logging_setup.setup_logging()  # no lanza
    assert logging_setup._configured is True


def test_handle_thread_exception_logs_and_ignores_system_exit(monkeypatch, caplog):
    import logging as _logging

    monkeypatch.setattr(logging_setup, "_configured", True)

    class Args:
        exc_type = RuntimeError
        exc_value = RuntimeError("hilo roto")
        exc_traceback = None
        thread = None

    with caplog.at_level(_logging.ERROR, logger="valeterna"):
        logging_setup._handle_thread_exception(Args())
    assert "Excepción en hilo" in caplog.text

    class SysExitArgs(Args):
        exc_type = SystemExit

    logging_setup._handle_thread_exception(SysExitArgs())  # no lanza, no registra
