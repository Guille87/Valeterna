"""Capa de textos traducibles (GDD §9.1)."""

from valeterna import i18n


def test_t_resolves_a_key_from_the_catalog():
    assert i18n.t("status.fractura_magica") == "fractura mágica"


def test_t_interpolates_kwargs():
    got = i18n.t("combat.enemy_succumbs", name="Goblin")
    assert "Goblin" in got


def test_t_returns_the_key_when_it_is_missing():
    assert i18n.t("no.existe.esta.clave") == "no.existe.esta.clave"


def test_t_degrades_safely_when_a_parameter_is_missing():
    # La plantilla espera {name}; si se pasan otros kwargs y falta {name}, no
    # revienta: devuelve la plantilla tal cual.
    assert "{name}" in i18n.t("combat.enemy_succumbs", otra_cosa="x")


def test_set_locale_falls_back_to_default_for_unknown_codes():
    i18n.set_locale("xx")
    assert i18n.get_locale() == "es"
    i18n.set_locale("es")


def test_es_is_always_available():
    assert "es" in i18n.available_locales()


def test_every_element_and_status_name_has_a_catalog_entry():
    from valeterna.combat.elements import ELEMENT_STATUS, ELEMENTS

    for element in ELEMENTS:
        assert i18n.t(f"element.{element}") != f"element.{element}"
    for status in ELEMENT_STATUS.values():
        assert i18n.t(f"status.{status}") != f"status.{status}"
