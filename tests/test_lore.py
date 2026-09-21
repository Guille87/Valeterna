"""Notas de lore y Diario (GDD §2, v0.13.0-c): lógica pura y validación del
contenido real."""

from valeterna.ui.exploration import _ZONE_SERVICES
from valeterna.world.lore import LoreNote, add_note, found_notes, has_note
from valeterna.world.map import LORE_NOTES, ZONES, note_for_sub_location


def _note(note_id="n1"):
    return LoreNote(id=note_id, zone_id="los_yermos", sub_location="Túmulo", title="T", text="x")


def test_add_note_is_new_once_and_idempotent(player):
    note = _note()

    assert not has_note(player, note)
    assert add_note(player, note) is True
    assert add_note(player, note) is False
    assert player.mundo["diario"] == ["n1"]
    assert has_note(player, note)


def test_found_notes_keep_discovery_order_and_skip_unknown_ids(player):
    catalog = {"a": _note("a"), "b": _note("b")}
    player.mundo["diario"] = ["b", "fantasma", "a"]

    assert [n.id for n in found_notes(player, catalog)] == ["b", "a"]


def test_diary_survives_a_save_and_load(player, tmp_save_dir):
    from valeterna.characters.player import Player
    from valeterna.characters.stats import Stats
    from valeterna.persistence.save_load import load_game, save_game

    player.mundo["diario"] = ["tablon_refugio", "hoja_de_cael"]
    save_game(player, [], [])

    loaded = Player(player.name, Stats(1, 1, 1, 1, 1))
    assert load_game(loaded) is not None
    assert loaded.mundo["diario"] == ["tablon_refugio", "hoja_de_cael"]


# --- Contenido real -----------------------------------------------------------


def test_note_ids_are_unique_and_every_note_points_at_a_real_sub_location():
    from valeterna.world.data import (
        bosque_de_los_susurros,
        canon_del_trueno,
        cienaga_de_los_ahogados,
        ciudadela_en_ruinas,
        corazon_de_la_brecha,
        los_yermos,
        piedrablanca,
        torre_de_los_arcanos,
    )

    modules = (
        piedrablanca,
        los_yermos,
        bosque_de_los_susurros,
        cienaga_de_los_ahogados,
        canon_del_trueno,
        torre_de_los_arcanos,
        ciudadela_en_ruinas,
        corazon_de_la_brecha,
    )
    all_notes = [n for m in modules for n in getattr(m, "LORE", ())]
    assert len(all_notes) == len({n.id for n in all_notes}) == len(LORE_NOTES)
    for note in all_notes:
        assert note.zone_id in ZONES
        assert note.sub_location in ZONES[note.zone_id].sub_locations, note.id
        assert note.title and note.text


def test_every_note_lives_in_the_module_of_its_own_zone():
    from valeterna.world.data import los_yermos

    assert {n.zone_id for n in getattr(los_yermos, "LORE", ())} == {"los_yermos"}


def test_each_sub_location_has_a_note_unless_it_has_a_service():
    """Un sub-lugar sin servicio propio tiene exactamente una nota; los que
    abren una tienda/forja/taberna no."""
    for zone in ZONES.values():
        for place in zone.sub_locations:
            note = note_for_sub_location(zone.id, place)
            if (zone.id, place) in _ZONE_SERVICES:
                assert note is None, (zone.id, place)
            else:
                assert note is not None, (zone.id, place)


def test_no_two_notes_share_a_sub_location():
    places = [(n.zone_id, n.sub_location) for n in LORE_NOTES.values()]
    assert len(places) == len(set(places))
