import pytest

from valeterna.config import settings


@pytest.fixture
def config_file(tmp_path, monkeypatch):
    """Redirige config.ini a un archivo temporal para no tocar el real."""
    path = tmp_path / "config.ini"
    monkeypatch.setattr(settings, "CONFIG_FILE", path)
    return path


def test_volume_round_trip(config_file):
    settings.save_config(0.3, 0.7)
    assert settings.load_config() == (0.3, 0.7)


def test_load_config_defaults_when_no_file(config_file):
    assert settings.load_config() == (settings.DEFAULT_MUSIC_VOLUME, settings.DEFAULT_SFX_VOLUME)


def test_load_config_defaults_when_file_is_corrupt(config_file):
    config_file.write_text("esto no es un ini válido = [[[", encoding="utf-8")
    assert settings.load_config() == (settings.DEFAULT_MUSIC_VOLUME, settings.DEFAULT_SFX_VOLUME)


def test_crash_reporting_is_unset_by_default(config_file):
    assert settings.load_crash_reporting() == settings.CRASH_REPORTS_UNSET


def test_crash_reporting_round_trip(config_file):
    settings.save_crash_reporting(True)
    assert settings.load_crash_reporting() is True
    settings.save_crash_reporting(False)
    assert settings.load_crash_reporting() is False


def test_saving_volume_preserves_crash_reporting_and_vice_versa(config_file):
    """Las escrituras son leer-modificar-escribir: ninguna sección pisa a la otra."""
    settings.save_crash_reporting(True)
    settings.save_config(0.1, 0.2)
    assert settings.load_crash_reporting() is True
    assert settings.load_config() == (0.1, 0.2)

    settings.save_crash_reporting(False)
    assert settings.load_config() == (0.1, 0.2)
    assert settings.load_crash_reporting() is False


def test_update_check_defaults_to_true_and_round_trips(config_file):
    assert settings.load_update_check() is True
    settings.save_update_check(False)
    assert settings.load_update_check() is False
    settings.save_update_check(True)
    assert settings.load_update_check() is True


def test_update_check_does_not_clash_with_the_other_sections(config_file):
    settings.save_config(0.3, 0.4)
    settings.save_crash_reporting(True)
    settings.save_update_check(False)

    assert settings.load_config() == (0.3, 0.4)
    assert settings.load_crash_reporting() is True
    assert settings.load_update_check() is False


def test_language_defaults_to_es_and_round_trips(config_file):
    assert settings.load_language() == "es"
    settings.save_language("en")
    assert settings.load_language() == "en"

    settings.save_config(0.2, 0.3)
    assert settings.load_language() == "en"  # no lo pisa otra sección


def test_crash_reporting_unset_when_value_is_garbage(config_file):
    config_file.write_text("[REPORTS]\nsend_crash_reports = quizás\n", encoding="utf-8")
    assert settings.load_crash_reporting() == settings.CRASH_REPORTS_UNSET
