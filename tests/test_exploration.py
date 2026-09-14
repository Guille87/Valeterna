"""Bucle de exploración por zona (GDD §8.1, v0.12.0-b). `ui/exploration.py`
está `omit`ido de la métrica de cobertura (igual que `ui/menus.py`, ver
pyproject.toml) por ser casi todo `input()`/`print()` encadenados, pero sigue
mereciendo tests — mismo criterio que `tests/test_menus.py`."""

from valeterna.ui import exploration


def test_explore_with_no_unlocked_enemies_reports_nothing_to_explore(player, capsys):
    exploration._explore(player, unlocked_enemies=[], defeated_enemies=[])

    assert "No hay nada que explorar todavía" in capsys.readouterr().out


def test_explore_rolls_an_encounter_against_a_zone_enemy(player, monkeypatch):
    # player.mundo["zona_actual"] por defecto es "piedrablanca" (sin roster);
    # forzamos Los Yermos para que haya un enemigo backbone que elegir.
    player.mundo["zona_actual"] = "los_yermos"
    calls = {}
    monkeypatch.setattr(exploration, "initiate_battle", lambda *a, **k: calls.update(kw=k, args=a))
    monkeypatch.setattr("valeterna.ui.exploration.random.random", lambda: 0.0)  # cae en "encuentro"
    monkeypatch.setattr("valeterna.ui.exploration.random.choice", lambda seq: seq[0])

    exploration._explore(player, unlocked_enemies=["Goblin"], defeated_enemies=[])

    assert calls  # initiate_battle se llamó


def test_explore_rolls_a_gold_discovery(player, monkeypatch):
    player.mundo["zona_actual"] = "los_yermos"
    gold_before = player.inventory.gold
    # Justo por encima del umbral de encuentro (0.65) -> cae en "hallazgo".
    monkeypatch.setattr("valeterna.ui.exploration.random.random", lambda: 0.70)
    monkeypatch.setattr("valeterna.ui.exploration.random.randint", lambda a, b: 7)

    exploration._explore(player, unlocked_enemies=["Goblin"], defeated_enemies=[])

    assert player.inventory.gold == gold_before + 7


def test_explore_rolls_nothing_of_interest(player, monkeypatch, capsys):
    player.mundo["zona_actual"] = "los_yermos"
    monkeypatch.setattr("valeterna.ui.exploration.random.random", lambda: 0.99)  # por encima de ambos umbrales

    exploration._explore(player, unlocked_enemies=["Goblin"], defeated_enemies=[])

    assert "no encuentras nada de interés" in capsys.readouterr().out


def test_explore_falls_back_to_any_unlocked_enemy_outside_the_zone_roster(player, monkeypatch):
    """Piedrablanca no tiene roster propio: Explorar no debe bloquearse si el
    jugador ya tiene algún enemigo desbloqueado."""
    calls = {}
    monkeypatch.setattr(exploration, "initiate_battle", lambda *a, **k: calls.update(k=1))
    monkeypatch.setattr("valeterna.ui.exploration.random.random", lambda: 0.0)
    monkeypatch.setattr("valeterna.ui.exploration.random.choice", lambda seq: seq[0])

    exploration._explore(player, unlocked_enemies=["Goblin"], defeated_enemies=[])

    assert calls


def test_sublocation_flow_with_places(monkeypatch, capsys):
    from valeterna.world.map import ZONES

    zone = ZONES["los_yermos"]
    monkeypatch.setattr(exploration.console, "ask", lambda *a, **k: str(len(zone.sub_locations) + 1))  # Volver

    exploration._sublocation_flow(zone)

    out = capsys.readouterr().out
    for place in zone.sub_locations:
        assert place in out


def test_sublocation_flow_without_places_reports_nothing(capsys):
    from valeterna.world.zone import Zone

    exploration._sublocation_flow(Zone(id="vacia", name="Vacía", theme=""))

    assert "No hay ningún sub-lugar" in capsys.readouterr().out


def test_travel_flow_fast_travels_to_a_visited_zone(player, monkeypatch):
    player.mundo["zona_actual"] = "los_yermos"
    player.mundo["zonas_visitadas"] = ["piedrablanca", "los_yermos"]
    monkeypatch.setattr(exploration.console, "ask", lambda *a, **k: "1")  # única opción: Piedrablanca

    exploration._travel_flow(player, unlocked_enemies=["Goblin"])

    assert player.mundo["zona_actual"] == "piedrablanca"


def test_travel_flow_offers_the_frontier_once_reachable(player, monkeypatch):
    monkeypatch.setattr(exploration.console, "ask", lambda *a, **k: "1")  # Los Yermos (frontera)

    exploration._travel_flow(player, unlocked_enemies=["Goblin"])

    assert player.mundo["zona_actual"] == "los_yermos"
    assert "los_yermos" in player.mundo["zonas_visitadas"]


def test_travel_flow_does_not_offer_an_unreachable_frontier(player, capsys):
    exploration._travel_flow(player, unlocked_enemies=[])  # Goblin aún no desbloqueado

    assert "No hay ningún sitio al que viajar todavía" in capsys.readouterr().out
    assert player.mundo["zona_actual"] == "piedrablanca"


def test_travel_flow_cancel_option_changes_nothing(player, monkeypatch):
    monkeypatch.setattr(exploration.console, "ask", lambda *a, **k: "2")  # Cancelar (Los Yermos=1, Cancelar=2)

    exploration._travel_flow(player, unlocked_enemies=["Goblin"])

    assert player.mundo["zona_actual"] == "piedrablanca"


def test_character_menu_returning_to_the_zone_is_none(player, monkeypatch):
    monkeypatch.setattr(exploration.console, "ask", lambda *a, **k: "11")  # Volver a la zona

    result = exploration._character_menu(player, [], [], is_admin=False)

    assert result is None


def test_character_menu_returning_to_the_main_menu_signals_it(player, monkeypatch):
    monkeypatch.setattr(exploration.console, "ask", lambda *a, **k: "12")  # Volver al Menú Principal

    result = exploration._character_menu(player, [], [], is_admin=False)

    assert result == "volver_menu"


def test_character_menu_shows_admin_panel_only_for_admins(player, monkeypatch, capsys):
    monkeypatch.setattr(exploration.console, "ask", lambda *a, **k: "12")  # Volver al Menú Principal

    exploration._character_menu(player, [], [], is_admin=False)
    assert "Panel de Admin" not in capsys.readouterr().out

    # Con Panel de Admin insertado, "Volver al Menú Principal" pasa a "13".
    monkeypatch.setattr(exploration.console, "ask", lambda *a, **k: "13")
    exploration._character_menu(player, [], [], is_admin=True)
    assert "Panel de Admin" in capsys.readouterr().out


def test_zone_loop_exits_to_main_menu_via_the_character_menu(player, monkeypatch):
    answers = iter(["4", "12"])  # Personaje -> Volver al Menú Principal
    monkeypatch.setattr(exploration.console, "ask", lambda *a, **k: next(answers))

    exploration.zone_loop(player, unlocked_enemies=[], defeated_enemies=[], is_admin=False)
    # Si no lanza y termina, el bucle salió correctamente.
