import contextlib
import io

from valeterna.characters.enemies.bandido import Bandido
from valeterna.characters.enemies.goblin import Goblin
from valeterna.characters.enemies.mage import Mago
from valeterna.characters.enemies.troll import Troll
from valeterna.combat.battle import (
    ENEMY_PROGRESSION,
    _attempt_flee,
    _execute_turn,
    _run_enemy_turn,
    _run_player_turn,
    initiate_battle,
)
from valeterna.items.equipment import Armor, Weapon


def test_victory_unlocks_next_enemy_and_grants_rewards(player, weak_enemy, monkeypatch):
    monkeypatch.setattr("valeterna.combat.battle.time.sleep", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("valeterna.combat.battle.console.ask", lambda prompt: "1")

    unlocked = ["Goblin"]
    defeated = []

    initiate_battle(player, weak_enemy, defeated, unlocked)

    assert "Goblin" in defeated
    assert ENEMY_PROGRESSION["Goblin"] in unlocked
    assert weak_enemy.gold_min <= player.inventory.gold <= weak_enemy.gold_max
    assert player.is_alive()
    assert player.enemy_kill_counts["Goblin"] == 1


def test_victory_drop_line_shows_type_and_equipment_stats(player, monkeypatch, capsys):
    from valeterna.characters.enemies.goblin import Goblin
    from valeterna.combat.battle import _handle_victory
    from valeterna.items.equipment import Armor
    from valeterna.items.potions.healing_potion import HealingPotion

    monkeypatch.setattr("valeterna.combat.battle.time.sleep", lambda *a, **k: None)
    g = Goblin()
    monkeypatch.setattr(
        g,
        "drop_item",
        lambda: [
            Armor("Perneras Test", "Ligeras.", 5, slot="perneras", evasion=3),
            HealingPotion("Poción Test", "Restaura 20 HP", 2, 20),
        ],
    )
    _handle_victory(player, g, [], ["Goblin"])

    import re

    out = re.sub(r"\x1b\[[0-9;]*m", "", capsys.readouterr().out)
    assert "Perneras Test (armadura · perneras):" in out
    assert "Evasión" in out  # las stats de la armadura aparecen
    assert "Poción Test (poción): Restaura 20 HP" in out
    assert "[Cura:" not in out  # la poción NO repite lo que hace


def test_battle_announces_who_has_the_initiative(player, weak_enemy, monkeypatch, capsys):
    from valeterna.combat.battle import initiate_battle

    monkeypatch.setattr("valeterna.combat.battle.time.sleep", lambda *a, **k: None)
    monkeypatch.setattr("valeterna.combat.battle.console.ask", lambda *a, **k: "1")
    weak_enemy.stats.speed = 999  # el enemigo es claramente más rápido

    initiate_battle(player, weak_enemy, ["Goblin"], ["Goblin"])

    assert "tiene la iniciativa" in capsys.readouterr().out


def test_initiative_message_matches_who_actually_acts_first_on_a_near_tie(player, weak_enemy, monkeypatch, capsys):
    """v0.14.0-c (feedback del usuario): con velocidades parecidas (10 vs 11)
    los dos cruzan el umbral ATB en el mismo tick, y ahí el turno del jugador
    se resuelve siempre primero — el mensaje debe anunciar al jugador, no solo
    comparar quién tiene más velocidad en crudo (que habría dicho el enemigo)."""
    from valeterna.combat.battle import initiate_battle

    monkeypatch.setattr("valeterna.combat.battle.time.sleep", lambda *a, **k: None)
    monkeypatch.setattr("valeterna.combat.battle.console.ask", lambda *a, **k: "1")
    player.stats.speed = 10
    weak_enemy.stats.speed = 11  # "más rápido" en crudo, pero cruza el umbral en el mismo tick

    initiate_battle(player, weak_enemy, ["Goblin"], ["Goblin"])

    out = capsys.readouterr().out
    assert f"{player.name} tiene la iniciativa" in out
    assert f"{weak_enemy.name} tiene la iniciativa" not in out


def test_enemy_turn_pauses_at_the_end_to_read_the_result(player, monkeypatch):
    from valeterna.characters.enemies.goblin import Goblin

    sleeps = []
    monkeypatch.setattr("valeterna.combat.battle.time.sleep", lambda s: sleeps.append(s))
    _run_enemy_turn(player, Goblin(), ["Goblin"], turbo=False, turn_no=2)
    assert len(sleeps) >= 2  # una antes de actuar y otra después de las barras


def test_player_turn_header_includes_the_class(player, weak_enemy, monkeypatch):
    from valeterna.characters.classes import CharClass, starting_stats
    from valeterna.characters.player import Player

    arc = Player("Mag", starting_stats(CharClass.ARCANISTA), char_class=CharClass.ARCANISTA)
    monkeypatch.setattr("valeterna.combat.battle._player_menu", lambda *a, **k: "atacar")
    import contextlib
    import io

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        _run_player_turn(arc, weak_enemy, ["Goblin"], is_auto=False, turn_no=3)
    assert "── Turno 3 · Mag (Arcanista) ──" in buf.getvalue()


def test_turbo_enemy_turn_still_shows_the_status_bars():
    import contextlib
    import io

    from valeterna.characters.enemies.goblin import Goblin
    from valeterna.characters.player import Player
    from valeterna.characters.stats import Stats

    p = Player("P", Stats(100, 100, 5, 10, 2))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        _run_enemy_turn(p, Goblin(), ["Goblin"], turbo=True, turn_no=2)
    out = buf.getvalue()
    assert "── Turno 2" in out
    assert "HP" in out


def test_victory_increments_kill_count_on_repeat_wins(player, monkeypatch):
    from valeterna.characters.enemies.goblin import Goblin

    monkeypatch.setattr("valeterna.combat.battle.time.sleep", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("valeterna.combat.battle.console.ask", lambda prompt: "1")

    unlocked = ["Goblin"]
    defeated = ["Goblin"]  # ya derrotado antes: la próxima victoria debe sumar, no reiniciar

    def weak_goblin():
        g = Goblin()
        g.stats.health = 1
        g.stats.max_health = 1
        g.ambush_done = True
        return g

    initiate_battle(player, weak_goblin(), defeated, unlocked)
    initiate_battle(player, weak_goblin(), defeated, unlocked)

    assert player.enemy_kill_counts["Goblin"] == 2


def test_defeat_penalizes_gold_and_fully_heals_player(player, monkeypatch):
    from valeterna.characters.enemies.orc import Orc

    strong_enemy = Orc()
    strong_enemy.stats.min_atk = strong_enemy.stats.max_atk = 500  # garantiza que mate al jugador en 1 golpe

    player.stats.health = player.stats.max_health
    player.inventory.gold = 90

    monkeypatch.setattr("valeterna.combat.battle.time.sleep", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("valeterna.combat.battle.console.ask", lambda prompt: "1")

    unlocked = ["Goblin", "Orco"]
    defeated = ["Goblin"]

    initiate_battle(player, strong_enemy, defeated, unlocked)

    assert player.stats.health == player.stats.max_health
    assert player.inventory.gold == 90 - (90 // 3)


def _weak_goblin():
    from valeterna.characters.enemies.goblin import Goblin

    g = Goblin()
    g.stats.health = g.stats.max_health = 1
    g.ambush_done = True
    return g


def test_initiate_battle_returns_victory(player, monkeypatch):
    monkeypatch.setattr("valeterna.combat.battle.time.sleep", lambda *a, **k: None)
    monkeypatch.setattr("valeterna.combat.battle.console.ask", lambda *a, **k: "1")

    outcome = initiate_battle(player, _weak_goblin(), ["Goblin"], ["Goblin"])

    assert outcome == "victory"


def test_ask_chain_count_parsing(monkeypatch):
    from valeterna.combat import battle

    def answer(value):
        monkeypatch.setattr(battle.console, "ask", lambda *a, **k: value)
        return battle._ask_chain_count()

    assert answer("") == 1
    assert answer("abc") == 1
    assert answer("3") == 3
    assert answer("999") == battle._MAX_CHAIN_BATTLES


def test_chain_runs_several_fights_when_player_picks_auto(player, monkeypatch):
    """El jugador activa la auto-batalla y pide 3 peleas: la pelea en curso
    cuenta como la 1, y se encadenan 2 más contra enemigos nuevos."""
    from valeterna.characters.enemies.goblin import Goblin

    monkeypatch.setattr("valeterna.combat.battle.time.sleep", lambda *a, **k: None)
    # Turno 1: "6" (auto) -> "3" peleas. A partir de ahí auto y "" para las pausas.
    answers = iter(["6", "3"])
    monkeypatch.setattr("valeterna.combat.battle.console.ask", lambda *a, **k: next(answers, ""))

    first = Goblin()
    first.stats.health = first.stats.max_health = 40  # aguanta a que el jugador elija auto
    first.ambush_done = True

    outcome = initiate_battle(player, first, ["Goblin"], ["Goblin"], enemy_factory=_weak_goblin)

    assert outcome == "victory"
    assert player.enemy_kill_counts["Goblin"] == 3


def test_chain_prints_a_loot_summary_at_the_end(player, monkeypatch, capsys):
    from valeterna.characters.enemies.goblin import Goblin

    monkeypatch.setattr("valeterna.combat.battle.time.sleep", lambda *a, **k: None)
    answers = iter(["6", "2"])
    monkeypatch.setattr("valeterna.combat.battle.console.ask", lambda *a, **k: next(answers, ""))

    first = Goblin()
    first.stats.health = first.stats.max_health = 30
    first.ambush_done = True
    gold_before = player.inventory.gold

    initiate_battle(player, first, ["Goblin"], ["Goblin"], enemy_factory=_weak_goblin)

    out = capsys.readouterr().out
    assert "BOTÍN DE LA CADENA" in out
    assert "Oro: +" in out
    assert "XP: +" in out
    assert player.inventory.gold > gold_before


def test_chain_loot_summary_labels_each_item_by_type(player, capsys):
    from valeterna.combat.battle import _print_chain_loot
    from valeterna.items.equipment import Armor, Weapon
    from valeterna.items.materials import Material
    from valeterna.items.potions.healing_potion import HealingPotion

    start = {"gold": 0, "xp": 0, "level": 1, "items": {}}
    player.inventory.gold = 94
    player.experience = 188
    player.inventory.add_item(HealingPotion("Poción de Salud", "desc", 2, 20), 3, announce=False)
    player.inventory.add_item(Material("Capa de Sombras", "desc", 1), announce=False)
    player.inventory.add_item(Weapon("Daga Robada", "desc", 5, damage=4), announce=False)
    player.inventory.add_item(Armor("Capucha de Ladrón", "desc", 5, slot="casco", max_health=10), announce=False)

    _print_chain_loot(player, start)
    import re

    out = re.sub(r"\x1b\[[0-9;]*m", "", capsys.readouterr().out)

    assert "Poción de Salud x3 (poción)" in out
    assert "Capa de Sombras (material de herrería)" in out
    assert "Daga Robada (arma)" in out
    assert "Capucha de Ladrón (armadura · casco)" in out


def test_single_fight_has_no_chain_loot_summary(player, weak_enemy, monkeypatch, capsys):
    monkeypatch.setattr("valeterna.combat.battle.time.sleep", lambda *a, **k: None)
    monkeypatch.setattr("valeterna.combat.battle.console.ask", lambda *a, **k: "1")

    initiate_battle(player, weak_enemy, ["Goblin"], ["Goblin"], enemy_factory=lambda: weak_enemy)

    assert "BOTÍN DE LA CADENA" not in capsys.readouterr().out


def test_chain_mode_can_switch_from_auto_to_turbo_mid_chain(player, weak_enemy, monkeypatch):
    """Tras pulsar 'Q' y volver a elegir en el menú, el modo de la cadena se
    actualiza (auto -> turbo) para las peleas que quedan."""
    from valeterna.combat import battle

    chain = {"factory": lambda: weak_enemy, "chosen": True, "count": 3, "mode": "auto"}
    monkeypatch.setattr("valeterna.combat.battle._player_menu", lambda *a, **k: "turbo")
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)

    battle._run_player_turn(player, weak_enemy, ["Goblin"], is_auto=False, chain=chain)

    assert chain["mode"] == "turbo"


def test_chain_stops_on_defeat(player, monkeypatch):
    """Auto-batalla de 5 peleas: gana la 1ª (goblin flojo) y cae en la 2ª contra
    un enemigo que pega letal. La cadena se detiene con desenlace 'defeat'."""
    from valeterna.characters.enemies.goblin import Goblin
    from valeterna.characters.enemies.orc import Orc

    monkeypatch.setattr("valeterna.combat.battle.time.sleep", lambda *a, **k: None)
    answers = iter(["6", "5"])
    monkeypatch.setattr("valeterna.combat.battle.console.ask", lambda *a, **k: next(answers, ""))

    first = Goblin()
    first.stats.health = first.stats.max_health = 1
    first.ambush_done = True

    def deadly_orc():
        o = Orc()
        o.stats.min_atk = o.stats.max_atk = 5000
        o.stats.speed = 999  # actúa antes que el jugador
        return o

    outcome = initiate_battle(player, first, ["Goblin", "Orco"], ["Goblin", "Orco"], enemy_factory=deadly_orc)

    assert outcome == "defeat"
    assert player.enemy_kill_counts["Goblin"] == 1


def test_troll_takes_double_damage_from_fire():
    troll = Troll()
    troll.stats.armor = 0
    physical_dmg = troll.take_damage(20)

    another_troll = Troll()
    another_troll.stats.armor = 0
    fire_dmg = another_troll.take_damage(20, element="fuego")

    assert fire_dmg == round(physical_dmg * 1.5)


def test_goblin_is_not_affected_by_fire_element():
    goblin = Goblin()
    goblin.stats.armor = 0
    normal_dmg = goblin.take_damage(10)

    another_goblin = Goblin()
    another_goblin.stats.armor = 0
    fire_dmg = another_goblin.take_damage(10, element="fuego")

    assert fire_dmg == normal_dmg


def test_enemy_default_on_turn_end_has_no_regen_by_default():
    # La mayoría de enemigos no son "aptos" para regenerar: stat base 0, no pasa nada.
    goblin = Goblin()
    goblin.stats.health = 10
    goblin.on_turn_end()
    assert goblin.stats.health == 10


def test_enemy_default_on_turn_end_applies_regen_when_stat_is_set():
    goblin = Goblin()
    goblin.stats.regen = 5
    goblin.stats.health = 10

    goblin.on_turn_end()

    assert goblin.stats.health == 15


def test_troll_regen_is_anchored_to_its_regen_stat(monkeypatch):
    # random.randint(a, b) real (sin mockear) para comprobar el rango exacto usado
    seen_ranges = []
    import valeterna.characters.enemies.troll as troll_module

    original_randint = troll_module.random.randint
    monkeypatch.setattr(
        troll_module.random, "randint", lambda a, b: seen_ranges.append((a, b)) or original_randint(a, b)
    )

    troll = Troll()
    troll.stats.health = 100  # deja hueco para curar
    troll.on_turn_end()

    assert seen_ranges == [(troll.stats.regen - 5, troll.stats.regen + 5)]


def test_enemy_take_damage_magical_uses_magic_resist_instead_of_armor():
    mago = Mago()
    mago.stats.armor = 100  # no debería influir en absoluto en daño mágico
    mago.stats.magic_resist = 20

    dealt = mago.take_damage(40, is_magical=True)

    assert dealt == 20  # 40 * 20/(20+20), con res. mágica, ignora la armadura


def test_enemy_take_damage_physical_still_uses_armor_by_default():
    mago = Mago()
    mago.stats.armor = 3
    mago.stats.magic_resist = 100  # no debería influir en absoluto en daño físico

    dealt = mago.take_damage(20)

    assert dealt == 17  # 20 - armor(3), ignora los 100 de resistencia mágica


def test_enemy_take_damage_armor_penetration_reduces_mitigation():
    mago = Mago()
    mago.stats.armor = 5

    dealt = mago.take_damage(20, armor_penetration=2)

    assert dealt == 17  # 20 - max(0, armor(5) - penetración(2))


def test_enemy_take_damage_magic_penetration_reduces_magic_resist_mitigation():
    mago = Mago()
    mago.stats.magic_resist = 5

    dealt = mago.take_damage(20, is_magical=True, magic_penetration=2)

    assert dealt == 17  # 20 - max(0, magic_resist(5) - penetración(2))


def test_execute_turn_applies_elemental_bonus_against_weak_enemy(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.player.random.randint", lambda a, b: 10)
    monkeypatch.setattr("valeterna.combat.battle.random.choice", lambda seq: "hit")
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)  # siempre acierta

    player.equipped_weapon = Weapon("Espada Flamígera", "desc", 15, damage=0, element="fuego")

    troll = Troll()
    troll.stats.armor = 0
    troll.stats.health = troll.stats.max_health = 1000

    before = troll.stats.health
    _execute_turn(player, troll, defeated_enemies=[])
    dealt = before - troll.stats.health

    assert dealt == 15  # 10 base * 1.5 (débil al fuego) - 0 armadura


def test_elemental_weapon_can_inflict_its_status_on_the_enemy(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.player.random.randint", lambda a, b: 10)
    monkeypatch.setattr("valeterna.combat.battle.random.choice", lambda seq: "hit")
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)  # acierta
    monkeypatch.setattr("valeterna.combat.battle.random.random", lambda: 0.0)  # el estado prende

    player.equipped_weapon = Weapon("Colmillo Venenoso", "desc", 14, damage=0, element="veneno")
    goblin = Goblin()

    _execute_turn(player, goblin, defeated_enemies=[])

    assert any(e["name"] == "veneno" for e in goblin.status_effects)


def test_disarmed_player_weapon_applies_no_element_or_status(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.player.random.randint", lambda a, b: 10)
    monkeypatch.setattr("valeterna.combat.battle.random.choice", lambda seq: "hit")
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)
    monkeypatch.setattr("valeterna.combat.battle.random.random", lambda: 0.0)

    player.equipped_weapon = Weapon("Colmillo Venenoso", "desc", 14, damage=0, element="veneno")
    player.apply_status("desarmado", 2)
    bandido = Bandido()  # débil a veneno x1.5
    bandido.stats.armor = 0
    bandido.stats.health = bandido.stats.max_health = 500

    before = bandido.stats.health
    _execute_turn(player, bandido, defeated_enemies=["Bandido"])

    assert bandido.status_effects == []  # sin veneno
    assert before - bandido.stats.health == 10  # 10 base, sin el x1.5 del elemento


def test_bandit_does_not_disarm_an_already_disarmed_player(player, monkeypatch):
    from valeterna.characters.enemies.bandido import Bandido

    monkeypatch.setattr("valeterna.characters.enemies.bandido.random.random", lambda: 0.0)  # querría desarmar
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)  # acierta
    monkeypatch.setattr("valeterna.characters.enemies.bandido.random.randint", lambda a, b: 10)

    bandido = Bandido()
    player.apply_status("desarmado", 2)
    hp_before = player.stats.health

    bandido.perform_turn(player)  # ya desarmado -> ataca en vez de re-desarmar

    assert player.stats.health < hp_before  # hizo daño, no otro desarme


def test_immobilized_player_still_gets_the_menu_and_can_use_an_item(player, weak_enemy, monkeypatch):
    monkeypatch.setattr("valeterna.combat.battle.console.ask", lambda prompt: "2")  # Objetos
    monkeypatch.setattr(player.inventory, "equip_menu", lambda *a, **k: True)  # "usó un objeto"
    monkeypatch.setattr("random.random", lambda: 0.0)  # parálisis segura

    player.apply_status("paralizado", 2)
    signal, _ = _run_player_turn(player, weak_enemy, defeated_enemies=[], is_auto=False)

    assert signal == "ok"
    assert weak_enemy.is_alive()  # no atacó (estaba inmovilizado), pero usó el objeto


def test_golem_is_immune_to_lightning_and_weak_to_ice():
    from valeterna.characters.enemies.golem import GolemDePiedra

    golem = GolemDePiedra()
    golem.stats.armor = 0
    assert golem.affinity_for({"rayo"}) == 0.0
    assert golem.affinity_for({"hielo"}) == 1.5
    assert golem.take_damage(50, element="rayo") == 0


def test_frozen_enemy_loses_the_turn_without_the_turn_header(player, monkeypatch):
    monkeypatch.setattr("valeterna.combat.battle.time.sleep", lambda *a: None)
    monkeypatch.setattr("random.random", lambda: 0.9)  # no se descongela

    goblin = Goblin()
    goblin.apply_status("congelado", 3)

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        _run_enemy_turn(player, goblin, defeated_enemies=["Goblin"], turn_no=1)
    out = buf.getvalue()

    assert "congelado" in out
    assert "── Turno" not in out  # no cabecera de turno cuando pierde el turno


def test_mage_spells_print_the_damage_dealt(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)  # acierta
    monkeypatch.setattr("valeterna.characters.enemies.mage.random.random", lambda: 0.99)  # sin crit/estado
    monkeypatch.setattr("valeterna.characters.enemies.mage.random.randint", lambda a, b: 10)

    mago = Mago()
    for spell in (mago._cast_fireball, mago._cast_thunder, mago._cast_poison, mago._cast_blizzard):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            spell(player)
        assert "de daño" in buf.getvalue()


def test_status_weapon_does_nothing_to_an_element_immune_enemy(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.player.random.randint", lambda a, b: 10)
    monkeypatch.setattr("valeterna.combat.battle.random.choice", lambda seq: "hit")
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)
    monkeypatch.setattr("valeterna.combat.battle.random.random", lambda: 0.0)

    player.equipped_weapon = Weapon("Colmillo Venenoso", "desc", 14, damage=0, element="veneno")
    goblin = Goblin()
    type(goblin).IMMUNE_ELEMENTS = frozenset({"veneno"})
    try:
        before = goblin.stats.health
        _execute_turn(player, goblin, defeated_enemies=[])
        assert goblin.status_effects == []
        assert goblin.stats.health == before  # inmune al elemento -> 0 daño
    finally:
        type(goblin).IMMUNE_ELEMENTS = frozenset()


def test_execute_turn_applies_elemental_bonus_for_newer_elements(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.player.random.randint", lambda a, b: 10)
    monkeypatch.setattr("valeterna.combat.battle.random.choice", lambda seq: "hit")
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)  # siempre acierta

    player.equipped_weapon = Weapon("Colmillo Venenoso", "desc", 14, damage=0, element="veneno")

    bandido = Bandido()
    bandido.stats.armor = 0
    bandido.stats.health = bandido.stats.max_health = 1000

    before = bandido.stats.health
    _execute_turn(player, bandido, defeated_enemies=[])
    dealt = before - bandido.stats.health

    assert dealt == 15  # 10 base * 1.5 (débil al veneno) - 0 armadura


def test_execute_turn_applies_crit_multiplier(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.player.random.randint", lambda a, b: 10)
    monkeypatch.setattr("valeterna.combat.battle.random.choice", lambda seq: "hit")
    monkeypatch.setattr("valeterna.combat.battle.random.random", lambda: 0.0)  # siempre crítico
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)  # siempre acierta

    player.equipped_armor["guantes"] = Armor("Guantes", "desc", 1, slot="guantes", crit_chance=1.0)
    player.stats.armor = 0

    goblin = Goblin()
    goblin.stats.armor = 0
    goblin.stats.health = goblin.stats.max_health = 1000

    before = goblin.stats.health
    _execute_turn(player, goblin, defeated_enemies=[])
    dealt = before - goblin.stats.health

    assert dealt == int(10 * player.stats.crit_damage)  # 10 base * 1.5 (multiplicador base)


def test_execute_turn_crit_uses_max_attack_not_the_dice_roll(player, monkeypatch):
    """v0.14.0-c (feedback del usuario): un crítico ya no multiplica la tirada
    normal — usa siempre el extremo alto del rango, para que nunca pueda salir
    más flojo que un golpe normal con suerte. Se fuerza `randint` a un valor
    bajo (1) precisamente para demostrar que el crítico lo ignora."""
    monkeypatch.setattr("valeterna.characters.player.random.randint", lambda a, b: 1)  # la tirada normal, ignorada
    monkeypatch.setattr("valeterna.combat.battle.random.choice", lambda seq: "hit")
    monkeypatch.setattr("valeterna.combat.battle.random.random", lambda: 0.0)  # siempre crítico
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)  # siempre acierta

    player.equipped_armor["guantes"] = Armor("Guantes", "desc", 1, slot="guantes", crit_chance=1.0)
    player.stats.armor = 0
    player.stats.min_atk, player.stats.max_atk = 5, 10

    goblin = Goblin()
    goblin.stats.armor = 0
    goblin.stats.health = goblin.stats.max_health = 1000

    before = goblin.stats.health
    _execute_turn(player, goblin, defeated_enemies=[])
    dealt = before - goblin.stats.health

    assert dealt == int(10 * player.stats.crit_damage)  # max_atk(10) * 1.5, no min(1) * 1.5


def test_execute_turn_skill_damage_uses_max_attack_not_the_dice_roll(player, monkeypatch):
    """Misma idea para una habilidad de daño (Golpe Firme): usa siempre el
    extremo alto del rango, con su propio multiplicador encima."""
    monkeypatch.setattr("valeterna.characters.player.random.randint", lambda a, b: 1)
    monkeypatch.setattr("valeterna.combat.battle.random.choice", lambda seq: "hit")
    monkeypatch.setattr("valeterna.combat.battle.random.random", lambda: 0.99)  # sin crítico
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)  # acierto garantizado igualmente

    player.stats.armor = 0
    player.stats.crit_chance = 0.0
    player.stats.min_atk, player.stats.max_atk = 5, 10

    goblin = Goblin()
    goblin.stats.armor = 0
    goblin.stats.health = goblin.stats.max_health = 1000

    before = goblin.stats.health
    _execute_turn(player, goblin, defeated_enemies=[], skill_params={"guaranteed_hit": True, "damage_mult": 1.4})
    dealt = before - goblin.stats.health

    assert dealt == int(10 * 1.4)  # max_atk(10) * 1.4, no min(1) * 1.4


def test_execute_turn_normal_attack_still_rolls_the_dice(player, monkeypatch):
    """Un ataque normal (sin habilidad ni crítico) no se ha tocado: sigue
    tirando el dado de siempre, incluso si el resultado es el mínimo."""
    monkeypatch.setattr("valeterna.characters.player.random.randint", lambda a, b: 1)
    monkeypatch.setattr("valeterna.combat.battle.random.choice", lambda seq: "hit")
    monkeypatch.setattr("valeterna.combat.battle.random.random", lambda: 0.99)  # sin crítico
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)  # acierto garantizado

    player.stats.armor = 0
    player.stats.crit_chance = 0.0
    player.stats.min_atk, player.stats.max_atk = 5, 10

    goblin = Goblin()
    goblin.stats.armor = 0
    goblin.stats.health = goblin.stats.max_health = 1000

    before = goblin.stats.health
    _execute_turn(player, goblin, defeated_enemies=[])
    dealt = before - goblin.stats.health

    assert dealt == 1  # la tirada mockeada, no el máximo


def test_execute_turn_uses_attacker_armor_penetration(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.player.random.randint", lambda a, b: 10)
    monkeypatch.setattr("valeterna.combat.battle.random.choice", lambda seq: "hit")
    # random.random() a 0.0 garantiza acierto (resolve_hit); como el jugador
    # tiene crit_chance=0.0 por defecto, is_crit sigue siendo False (0.0 < 0.0 es falso).
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)
    monkeypatch.setattr("valeterna.combat.battle.random.random", lambda: 0.0)

    player.stats.armor_penetration = 20

    goblin = Goblin()
    goblin.stats.armor = 40
    goblin.stats.health = goblin.stats.max_health = 1000

    before = goblin.stats.health
    _execute_turn(player, goblin, defeated_enemies=[])
    dealt = before - goblin.stats.health

    # 10 base, armadura efectiva 40-20=20 -> round(10 * 20/40) = 5.
    # Sin la penetración serían round(10 * 20/60) = 3.
    assert dealt == 5


def test_execute_turn_uses_element_from_bracers_when_no_elemental_weapon(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.player.random.randint", lambda a, b: 10)
    monkeypatch.setattr("valeterna.combat.battle.random.choice", lambda seq: "hit")
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)  # siempre acierta

    player.equipped_weapon = Weapon("Espada de Hierro", "desc", 10, damage=0)  # sin elemento
    player.equipped_armor["brazales"] = Armor("Brazales Arcanos", "desc", 1, slot="brazales", element="fuego")
    player.stats.armor = 0

    troll = Troll()
    troll.stats.armor = 0
    troll.stats.health = troll.stats.max_health = 1000

    before = troll.stats.health
    _execute_turn(player, troll, defeated_enemies=[])
    dealt = before - troll.stats.health

    assert dealt == 15  # 10 base * 1.5 (débil al fuego, heredado de los brazales)


def _strip_ansi(text: str) -> str:
    import re

    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def test_super_effective_message_uses_correct_gender_for_oscuridad(player, monkeypatch, capsys):
    # A petición del usuario: "la oscuridad", no "el oscuridad" (el resto de
    # elementos son masculinos y ya funcionaban bien).
    from valeterna.characters.enemies.angel_caido import AngelCaido

    monkeypatch.setattr("valeterna.characters.player.random.randint", lambda a, b: 10)
    monkeypatch.setattr("valeterna.combat.battle.random.choice", lambda seq: "hit")
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)  # siempre acierta

    player.equipped_weapon = Weapon("Daga Umbría", "desc", 14, damage=0, element="oscuridad")
    angel = AngelCaido()  # débil a oscuridad
    _execute_turn(player, angel, defeated_enemies=[])

    out = _strip_ansi(capsys.readouterr().out)
    assert "La oscuridad causa estragos" in out
    assert "El oscuridad" not in out


def test_non_arcanista_wielding_a_magical_element_weapon_deals_magical_damage(player, monkeypatch):
    # v0.11.0-b: lo mágico/físico es propiedad del elemento, no de la clase —
    # cualquiera con un arma sagrado/oscuridad/arcano golpea mágico.
    from valeterna.characters.enemies.goblin import Goblin

    monkeypatch.setattr("valeterna.characters.player.random.randint", lambda a, b: 10)
    monkeypatch.setattr("valeterna.combat.battle.random.choice", lambda seq: "hit")
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)  # siempre acierta

    player.equipped_weapon = Weapon("Espada Consagrada", "desc", 14, damage=0, element="sagrado")
    assert player.is_magical_attacker() is False  # el jugador de pruebas no es Arcanista

    goblin = Goblin()
    calls = {}
    original_take_damage = goblin.take_damage
    monkeypatch.setattr(
        goblin, "take_damage", lambda damage, **kw: (calls.update(kw), original_take_damage(damage, **kw))[1]
    )

    _execute_turn(player, goblin, defeated_enemies=[])

    assert calls.get("is_magical") is True
    assert calls.get("element") == "sagrado"


def test_non_arcanista_wielding_a_physical_element_weapon_deals_physical_damage(player, monkeypatch):
    from valeterna.characters.enemies.goblin import Goblin

    monkeypatch.setattr("valeterna.characters.player.random.randint", lambda a, b: 10)
    monkeypatch.setattr("valeterna.combat.battle.random.choice", lambda seq: "hit")
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)  # siempre acierta

    player.equipped_weapon = Weapon("Espada Flamígera", "desc", 14, damage=0, element="fuego")

    goblin = Goblin()
    calls = {}
    original_take_damage = goblin.take_damage
    monkeypatch.setattr(
        goblin, "take_damage", lambda damage, **kw: (calls.update(kw), original_take_damage(damage, **kw))[1]
    )

    _execute_turn(player, goblin, defeated_enemies=[])

    assert not calls.get("is_magical")  # ni pasado ni True: se mitiga con armadura
    assert calls.get("element") == "fuego"


def test_immune_element_hit_does_not_also_print_a_blocked_message(player, monkeypatch, capsys):
    from valeterna.characters.enemies.gargola import Gargola

    monkeypatch.setattr("valeterna.characters.player.random.randint", lambda a, b: 10)
    monkeypatch.setattr("valeterna.combat.battle.random.choice", lambda seq: "hit")
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)  # siempre acierta

    player.equipped_weapon = Weapon("Colmillo Venenoso", "desc", 14, damage=0, element="veneno")

    gargola = Gargola()  # inmune al veneno
    _execute_turn(player, gargola, defeated_enemies=[])

    out = _strip_ansi(capsys.readouterr().out)
    assert "inmune al veneno" in out
    assert "ha bloqueado el ataque" not in out


def test_veneno_de_contacto_announces_immunity_instead_of_staying_silent(player, monkeypatch, capsys):
    from valeterna.characters.enemies.espiritu_vengativo import EspirituVengativo

    monkeypatch.setattr("valeterna.characters.player.random.randint", lambda a, b: 10)
    monkeypatch.setattr("valeterna.combat.battle.random.choice", lambda seq: "hit")
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)  # siempre acierta y siempre procs
    monkeypatch.setattr(player, "passive_param", lambda skill_id, key, default=0.0: 1.0)

    player.equipped_weapon = Weapon("Espada de Hierro", "desc", 10, damage=0)  # sin elemento

    espiritu = EspirituVengativo()  # inmune al veneno
    _execute_turn(player, espiritu, defeated_enemies=[])

    out = _strip_ansi(capsys.readouterr().out)
    assert "inmune al veneno" in out
    assert "envenena" not in out


def test_execute_turn_deals_no_damage_on_a_miss(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.player.random.randint", lambda a, b: 10)
    monkeypatch.setattr("valeterna.combat.battle.random.choice", lambda seq: "hit")
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.99)  # siempre falla

    goblin = Goblin()
    before = goblin.stats.health
    _execute_turn(player, goblin, defeated_enemies=[])

    assert goblin.stats.health == before  # el fallo no llega a restar vida


def test_enemy_default_perform_turn_deals_no_damage_on_a_miss(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.99)  # siempre falla
    # Con acierto base 100%, solo la evasión hace que un ataque pueda fallar.
    player.stats.evasion = 50

    goblin = Goblin()
    before = player.stats.health
    goblin.perform_turn(player)

    assert player.stats.health == before  # el fallo no llega a restar vida


def test_enemy_default_perform_turn_applies_crit_multiplier(player, monkeypatch):
    """v0.14.0-c (feedback del usuario): igual que el jugador, un crítico
    enemigo ya no multiplica otra tirada — usa siempre `max_atk`. Se mockea
    `randint` a un valor bajo (1) precisamente para demostrar que el crítico
    lo ignora."""
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)  # siempre acierta y critea
    monkeypatch.setattr("valeterna.characters.enemies.enemy_base.random.randint", lambda a, b: 1)
    player.stats.armor = 0

    goblin = Goblin()
    before = player.stats.health
    goblin.perform_turn(player)
    dealt = before - player.stats.health

    assert dealt == int(goblin.stats.max_atk * goblin.stats.crit_damage)  # max_atk * 1.6, no 1 * 1.6


def test_attempt_flee_is_always_successful_when_player_is_at_least_as_fast(player):
    troll = Troll()  # speed 5, jugador speed 10 -> jugador es más rápido -> 100%
    assert player.stats.speed >= troll.stats.speed
    for _ in range(20):
        assert _attempt_flee(player, troll) is True


def test_attempt_flee_chance_drops_but_never_reaches_zero_when_enemy_is_faster(player, monkeypatch):
    mago = Mago()  # speed 15, jugador speed 10 -> jugador es más lento -> 10/15 = 0.6667

    monkeypatch.setattr("valeterna.combat.battle.random.random", lambda: 0.66)
    assert _attempt_flee(player, mago) is True

    monkeypatch.setattr("valeterna.combat.battle.random.random", lambda: 0.67)
    assert _attempt_flee(player, mago) is False

    # Nunca debería ser exactamente 0: random.random() siempre está en [0, 1),
    # así que con un flee_chance positivo (aunque pequeño) sigue siendo posible.
    monkeypatch.setattr("valeterna.combat.battle.random.random", lambda: 0.0)
    assert _attempt_flee(player, mago) is True


def test_fleeing_does_not_heal_damage_carried_over_from_before_the_battle(player, weak_enemy, monkeypatch):
    monkeypatch.setattr("valeterna.combat.battle.time.sleep", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("valeterna.combat.battle.console.ask", lambda prompt: "4")  # huir
    monkeypatch.setattr("valeterna.combat.battle._attempt_flee", lambda *a, **k: True)

    player.stats.max_health = 100
    player.stats.health = 40  # ya venía dañado de una pelea anterior (missing=60)

    initiate_battle(player, weak_enemy, defeated_enemies=[], unlocked_enemies=["Goblin"])

    # Huir resuelve antes que cualquier turno del enemigo, así que no se pierde
    # vida EN esta pelea: la curación de después de combate no debe tocar nada.
    assert player.stats.health == 40


def test_run_player_turn_failed_flee_consumes_turn_without_attacking(player, weak_enemy, monkeypatch):
    weak_enemy.stats.max_health = 50
    weak_enemy.stats.health = 50
    monkeypatch.setattr("valeterna.combat.battle.console.ask", lambda prompt: "4")
    monkeypatch.setattr("valeterna.combat.battle._attempt_flee", lambda *a, **k: False)

    signal, is_auto = _run_player_turn(player, weak_enemy, defeated_enemies=[], is_auto=False)

    assert signal == "ok"
    assert is_auto is False
    assert weak_enemy.stats.health == 50  # la huida fallida consume el turno, no ataca


def test_run_player_turn_successful_flee_returns_huir_signal(player, weak_enemy, monkeypatch):
    monkeypatch.setattr("valeterna.combat.battle.console.ask", lambda prompt: "4")
    monkeypatch.setattr("valeterna.combat.battle._attempt_flee", lambda *a, **k: True)

    signal, is_auto = _run_player_turn(player, weak_enemy, defeated_enemies=[], is_auto=False)

    assert signal == "huir"


def test_defending_halves_incoming_damage(player):
    player.stats.armor = 0
    player.stats.max_health = 100
    player.stats.health = 100

    player.defending = True
    dealt = player.take_damage(40)

    assert dealt == 20
    assert player.stats.health == 80


def test_run_player_turn_defender_sets_the_stance_and_consumes_the_turn(player, weak_enemy, monkeypatch):
    weak_enemy.stats.max_health = 50
    weak_enemy.stats.health = 50
    monkeypatch.setattr("valeterna.combat.battle.console.ask", lambda prompt: "2")  # Defender

    signal, _ = _run_player_turn(player, weak_enemy, defeated_enemies=[], is_auto=False)

    assert signal == "ok"
    assert player.defending is True
    assert weak_enemy.stats.health == 50  # defender no ataca


def test_defending_is_cleared_when_the_players_next_turn_begins(player, weak_enemy, monkeypatch):
    monkeypatch.setattr("valeterna.combat.battle.console.ask", lambda prompt: "1")  # atacar
    player.defending = True

    _run_player_turn(player, weak_enemy, defeated_enemies=[], is_auto=False)

    assert player.defending is False


def test_turbo_option_is_offered_only_for_defeated_enemies(player, weak_enemy, monkeypatch):
    from valeterna.combat.battle import _player_menu

    monkeypatch.setattr("valeterna.combat.battle.console.ask", lambda prompt: "7")
    assert _player_menu(player, weak_enemy, defeated_enemies=[weak_enemy.name]) == "turbo"


def test_player_menu_options_are_in_the_requested_order(player, weak_enemy, monkeypatch, capsys):
    """Orden pedido por el usuario: Atacar, Habilidades, Defender, Objetos,
    Huir, Info, Auto-Batalla, Auto-Batalla Turbo (Habilidades solo si hay
    activas equipadas)."""
    from valeterna.combat.battle import _player_menu

    monkeypatch.setattr("valeterna.combat.battle.console.ask", lambda prompt: "1")

    _player_menu(player, weak_enemy, defeated_enemies=[weak_enemy.name])
    line = capsys.readouterr().out.splitlines()[0]
    assert line == (
        "1. Atacar | 2. Defender | 3. Objetos | 4. Huir | 5. Info | 6. Auto-Batalla | 7. Auto-Batalla Turbo"
    )

    player.equipped_skills = ["golpe_firme"]
    _player_menu(player, weak_enemy, defeated_enemies=[weak_enemy.name])
    line = capsys.readouterr().out.splitlines()[0]
    assert line == (
        "1. Atacar | 2. Habilidades | 3. Defender | 4. Objetos | 5. Huir | "
        "6. Info | 7. Auto-Batalla | 8. Auto-Batalla Turbo"
    )


def test_turbo_auto_battle_runs_without_any_sleep(player, monkeypatch):
    from valeterna.characters.enemies.goblin import Goblin

    slept = []
    monkeypatch.setattr("valeterna.combat.battle.time.sleep", lambda *a, **k: slept.append(a))
    monkeypatch.setattr("valeterna.combat.battle.console.ask", lambda prompt: "7")  # Auto turbo
    monkeypatch.setattr("valeterna.combat.battle.check_for_interrupt", lambda: False)

    enemy = Goblin()
    enemy.stats.min_atk = enemy.stats.max_atk = 1
    initiate_battle(player, enemy, defeated_enemies=["Goblin"], unlocked_enemies=["Goblin"])

    assert player.is_alive()
    assert slept == []  # turbo: cero pausas, ni de turno ni el "Presiona Enter" final
