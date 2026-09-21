"""Bucle de exploración por zona (GDD §8.1, v0.12.0-b/c). `ui/exploration.py`
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


def test_sublocation_flow_with_places(player, monkeypatch, capsys):
    from valeterna.world.map import ZONES

    zone = ZONES["los_yermos"]
    monkeypatch.setattr(exploration.console, "ask", lambda *a, **k: str(len(zone.sub_locations) + 1))  # Volver

    exploration._sublocation_flow(player, zone)

    out = capsys.readouterr().out
    for place in zone.sub_locations:
        assert place in out


def test_sublocation_flow_without_places_reports_nothing(player, capsys):
    from valeterna.world.zone import Zone

    exploration._sublocation_flow(player, Zone(id="vacia", name="Vacía", theme=""))

    assert "No hay ningún sub-lugar" in capsys.readouterr().out


def test_sublocation_flow_opens_the_shop_at_piedrablancas_mercado(player, monkeypatch):
    from valeterna.world.map import ZONES

    zone = ZONES["piedrablanca"]
    mercado_idx = zone.sub_locations.index("Mercado") + 1
    monkeypatch.setattr(exploration.console, "ask", lambda *a, **k: str(mercado_idx))
    opened = {}
    monkeypatch.setitem(exploration._ZONE_SERVICES, ("piedrablanca", "Mercado"), lambda p: opened.update(player=p))

    exploration._sublocation_flow(player, zone)

    assert opened.get("player") is player


def test_sublocation_flow_opens_the_forge_at_piedrablancas_herreria(player, monkeypatch):
    from valeterna.world.map import ZONES

    zone = ZONES["piedrablanca"]
    herreria_idx = zone.sub_locations.index("Herrería") + 1
    monkeypatch.setattr(exploration.console, "ask", lambda *a, **k: str(herreria_idx))
    opened = {}
    monkeypatch.setitem(exploration._ZONE_SERVICES, ("piedrablanca", "Herrería"), lambda p: opened.update(player=p))

    exploration._sublocation_flow(player, zone)

    assert opened.get("player") is player


def test_sublocation_flow_opens_rest_at_piedrablancas_taberna(player, monkeypatch):
    from valeterna.world.map import ZONES

    zone = ZONES["piedrablanca"]
    taberna_idx = zone.sub_locations.index("Taberna") + 1
    monkeypatch.setattr(exploration.console, "ask", lambda *a, **k: str(taberna_idx))
    opened = {}
    monkeypatch.setitem(exploration._ZONE_SERVICES, ("piedrablanca", "Taberna"), lambda p: opened.update(player=p))

    exploration._sublocation_flow(player, zone)

    assert opened.get("player") is player


def _visit(player, monkeypatch, zone_id, place):
    from valeterna.world.map import ZONES

    zone = ZONES[zone_id]
    idx = zone.sub_locations.index(place) + 1
    monkeypatch.setattr(exploration.console, "ask", lambda *a, **k: str(idx))
    exploration._sublocation_flow(player, zone)


def test_first_visit_to_a_sub_location_shows_its_note_and_saves_it(player, monkeypatch, capsys):
    _visit(player, monkeypatch, "piedrablanca", "Refugio")

    out = capsys.readouterr().out
    assert "Tablón del Refugio" in out
    assert "Ena" in out
    assert player.mundo["diario"] == ["tablon_refugio"]


def test_first_visit_to_a_sub_location_pauses_after_the_note_but_a_repeat_does_not(player, monkeypatch):
    from valeterna.world.map import ZONES

    zone = ZONES["piedrablanca"]
    idx = str(zone.sub_locations.index("Refugio") + 1)
    prompts = []

    def ask(prompt="", *a, **k):
        prompts.append(prompt)
        return idx if "Elige un lugar" in prompt else ""

    monkeypatch.setattr(exploration.console, "ask", ask)

    exploration._sublocation_flow(player, zone)
    assert "Presiona Enter para continuar" in prompts[-1]

    prompts.clear()
    exploration._sublocation_flow(player, zone)
    assert not any("Presiona Enter" in p for p in prompts)


def test_revisiting_a_sub_location_does_not_repeat_the_note(player, monkeypatch, capsys):
    _visit(player, monkeypatch, "piedrablanca", "Refugio")
    capsys.readouterr()

    _visit(player, monkeypatch, "piedrablanca", "Refugio")

    out = capsys.readouterr().out
    assert "Ya has leído" in out
    assert "Ena" not in out
    assert player.mundo["diario"] == ["tablon_refugio"]


def test_sub_location_without_a_note_is_still_a_stub(player, monkeypatch, capsys):
    monkeypatch.setattr(exploration, "note_for_sub_location", lambda zone_id, place: None)

    _visit(player, monkeypatch, "los_yermos", "Túmulo")

    assert "todavía no hay nada que hacer aquí" in capsys.readouterr().out
    assert player.mundo["diario"] == []


def test_diary_flow_reports_when_empty(player, capsys):
    exploration._diary_flow(player)

    assert "Todavía no has encontrado ninguna nota" in capsys.readouterr().out


def test_diary_flow_lists_found_notes_by_zone_and_rereads_one(player, monkeypatch, capsys):
    # Orden de descubrimiento distinto al del mapa: el Diario debe ordenar por zona.
    player.mundo["diario"] = ["hoja_de_cael", "tablon_refugio"]
    answers = iter(["2", "", "3"])  # 2ª nota (la de Cael), Enter, Volver
    monkeypatch.setattr(exploration.console, "ask", lambda *a, **k: next(answers))

    exploration._diary_flow(player)

    out = capsys.readouterr().out
    assert out.index("Tablón del Refugio") < out.index("Hoja suelta de Cael")
    assert out.index("Piedrablanca") < out.index("Los Yermos")
    assert "Noche 41" in out  # se ha releído la nota elegida


def test_diary_flow_rejects_invalid_choices(player, monkeypatch, capsys):
    player.mundo["diario"] = ["tablon_refugio"]
    answers = iter(["x", "9", "2"])  # inválida, fuera de rango, Volver
    monkeypatch.setattr(exploration.console, "ask", lambda *a, **k: next(answers))

    exploration._diary_flow(player)

    assert capsys.readouterr().out.count("Opción no válida.") == 2


def test_diary_flow_ignores_unknown_ids_from_old_saves(player, monkeypatch, capsys):
    player.mundo["diario"] = ["nota_que_ya_no_existe"]

    exploration._diary_flow(player)

    assert "Todavía no has encontrado ninguna nota" in capsys.readouterr().out


def test_character_menu_shows_the_diary_counter(player, monkeypatch, capsys):
    from valeterna.world.map import LORE_NOTES

    player.mundo["diario"] = ["tablon_refugio"]
    monkeypatch.setattr(exploration.console, "ask", lambda *a, **k: "10")  # Volver a la zona

    exploration._character_menu(player, [], [], is_admin=False)

    assert f"Diario (1/{len(LORE_NOTES)})" in capsys.readouterr().out


def test_rest_flow_heals_and_clears_status_for_gold(player, monkeypatch):
    player.stats.health = 1
    player.apply_status("veneno", 3)
    player.level = 2
    player.inventory.gold = 100
    monkeypatch.setattr(exploration.console, "ask", lambda *a, **k: "s")

    exploration._rest_flow(player)

    assert player.stats.health == player.stats.max_health
    assert player.status_effects == []
    assert player.inventory.gold == 100 - (exploration._REST_COST_PER_LEVEL * 2)


def test_rest_flow_declines_without_confirmation(player, monkeypatch):
    player.stats.health = 1
    gold_before = player.inventory.gold
    monkeypatch.setattr(exploration.console, "ask", lambda *a, **k: "n")

    exploration._rest_flow(player)

    assert player.stats.health == 1
    assert player.inventory.gold == gold_before


def test_rest_flow_refuses_without_enough_gold(player, monkeypatch, capsys):
    player.stats.health = 1
    player.inventory.gold = 0
    monkeypatch.setattr(exploration.console, "ask", lambda *a, **k: "s")

    exploration._rest_flow(player)

    assert player.stats.health == 1
    assert "No tienes oro suficiente" in capsys.readouterr().out


def test_rest_flow_reports_nothing_needed_when_already_at_full_health(player, capsys):
    exploration._rest_flow(player)

    assert "Ya estás a plena forma" in capsys.readouterr().out


def test_discovery_rolls_a_potion(player, monkeypatch):
    monkeypatch.setattr("valeterna.ui.exploration.random.random", lambda: 0.0)  # < _DISCOVERY_POTION_CHANCE

    exploration._discovery(player)

    assert player.inventory.quantities.get("Poción de Salud") == 1


def test_discovery_rolls_gold(player, monkeypatch):
    gold_before = player.inventory.gold
    monkeypatch.setattr("valeterna.ui.exploration.random.random", lambda: 0.99)
    monkeypatch.setattr("valeterna.ui.exploration.random.randint", lambda a, b: 5)

    exploration._discovery(player)

    assert player.inventory.gold == gold_before + 5


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
    monkeypatch.setattr(exploration.console, "ask", lambda *a, **k: "10")  # Volver a la zona

    result = exploration._character_menu(player, [], [], is_admin=False)

    assert result is None


def test_character_menu_returning_to_the_main_menu_signals_it(player, monkeypatch):
    monkeypatch.setattr(exploration.console, "ask", lambda *a, **k: "11")  # Volver al Menú Principal

    result = exploration._character_menu(player, [], [], is_admin=False)

    assert result == "volver_menu"


def test_character_menu_shows_admin_panel_only_for_admins(player, monkeypatch, capsys):
    monkeypatch.setattr(exploration.console, "ask", lambda *a, **k: "11")  # Volver al Menú Principal

    exploration._character_menu(player, [], [], is_admin=False)
    assert "Panel de Admin" not in capsys.readouterr().out

    # Con Panel de Admin insertado, "Volver al Menú Principal" pasa a "12".
    monkeypatch.setattr(exploration.console, "ask", lambda *a, **k: "12")
    exploration._character_menu(player, [], [], is_admin=True)
    assert "Panel de Admin" in capsys.readouterr().out


def test_zone_loop_exits_to_main_menu_via_the_character_menu(player, monkeypatch):
    answers = iter(["5", "11"])  # Personaje -> Volver al Menú Principal
    monkeypatch.setattr(exploration.console, "ask", lambda *a, **k: next(answers))

    exploration.zone_loop(player, unlocked_enemies=[], defeated_enemies=[], is_admin=False)
    # Si no lanza y termina, el bucle salió correctamente.


def test_talk_flow_without_npcs_reports_nobody_to_talk_to(player, capsys):
    from valeterna.world.map import ZONES

    exploration._talk_flow(player, ZONES["corazon_de_la_brecha"])

    assert "No hay nadie con quien hablar" in capsys.readouterr().out


def test_talk_flow_lists_the_zones_npcs_and_can_go_back(player, monkeypatch, capsys):
    from valeterna.world.map import ZONES

    monkeypatch.setattr(exploration.console, "ask", lambda *a, **k: "5")  # Volver (4 NPCs + Volver)

    exploration._talk_flow(player, ZONES["piedrablanca"])

    assert "Yerma" in capsys.readouterr().out


def test_talk_flow_plays_a_conversation_end_to_end(player, monkeypatch, capsys):
    from valeterna.world.map import ZONES

    # Yerma (1) -> "Solo busco una cama..." (2) -> primera respuesta (1) -> Enter
    answers = iter(["1", "2", "1", ""])
    monkeypatch.setattr(exploration.console, "ask", lambda *a, **k: next(answers))

    exploration._talk_flow(player, ZONES["piedrablanca"])

    assert "conocio_a_yerma" in player.mundo["banderas"]
    assert "yerma_intro/cama/0" in player.mundo["dialogos_vistos"]
    assert "yerma_intro" not in player.mundo["dialogos_vistos"]  # aún quedan ramas por hablar
    assert "Yerma" in capsys.readouterr().out


def test_talk_flow_pauses_after_the_npcs_last_line(player, monkeypatch):
    from valeterna.world.map import ZONES

    prompts = []
    answers = iter(["1", "2", "1", ""])

    def ask(prompt="", *a, **k):
        prompts.append(prompt)
        return next(answers)

    monkeypatch.setattr(exploration.console, "ask", ask)

    exploration._talk_flow(player, ZONES["piedrablanca"])

    assert "Presiona Enter para continuar" in prompts[-1]


def test_talk_flow_pauses_after_an_idle_line_too(player, monkeypatch):
    from valeterna.world.map import ZONES

    player.mundo["dialogos_vistos"].add("yerma_intro")  # ya agotada: solo líneas sueltas
    prompts = []
    answers = iter(["1", ""])

    def ask(prompt="", *a, **k):
        prompts.append(prompt)
        return next(answers)

    monkeypatch.setattr(exploration.console, "ask", ask)

    exploration._talk_flow(player, ZONES["piedrablanca"])

    assert "Presiona Enter para continuar" in prompts[-1]


def test_pick_reply_reprompts_until_valid(monkeypatch):
    answers = iter(["x", "9", "2"])
    monkeypatch.setattr(exploration.console, "ask", lambda *a, **k: next(answers))

    assert exploration._pick_reply(["a", "b", "c"], [False, False, False]) == 1


def test_pick_reply_puts_a_check_next_to_exhausted_replies(monkeypatch, capsys):
    monkeypatch.setattr(exploration.console, "ask", lambda *a, **k: "1")

    exploration._pick_reply(["uno", "dos", "tres"], [False, True, False])

    lines = [line for line in capsys.readouterr().out.splitlines() if "uno" in line or "dos" in line or "tres" in line]
    assert "✔" not in lines[0]
    assert "✔" in lines[1]
    assert "✔" not in lines[2]


def test_lore_texts_with_status_words_are_not_tinted(player, monkeypatch, capsys):
    """ "quemado/quemada" en un título de nota o en un nombre de sub-lugar es
    solo una palabra, no el estado alterado: no debe salir en rojo."""
    from colorama import Fore

    _visit(player, monkeypatch, "ciudadela_en_ruinas", "Plaza")  # nota "Bando quemado"
    _visit(player, monkeypatch, "bosque_de_los_susurros", "Cabaña quemada")  # 1ª visita: nota
    _visit(player, monkeypatch, "bosque_de_los_susurros", "Cabaña quemada")  # repetida: "Recorres ..."
    out = capsys.readouterr().out

    assert "Bando quemado" in out
    assert "Cabaña quemada" in out
    assert Fore.RED not in out
