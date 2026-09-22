from valeterna.characters.enemies.goblin import Goblin
from valeterna.characters.enemies.troll import Troll
from valeterna.ui.formatting import (
    print_bestiary_entry,
    print_player_enemy_info,
    print_status,
)


def test_print_status_renders_both_health_bars(player, capsys):
    enemy = Goblin()
    print_status(player, enemy, defeated_enemies=[enemy.name])
    out = capsys.readouterr().out
    assert player.name in out
    assert enemy.name in out
    assert f"{player.stats.health}/{player.stats.max_health} HP" in out


def test_print_status_hides_undefeated_enemy_health(player, capsys):
    enemy = Goblin()
    print_status(player, enemy, defeated_enemies=[])
    out = capsys.readouterr().out
    assert "??/?? HP" in out


def test_print_player_enemy_info_hides_stats_of_undefeated_enemy(player, capsys):
    enemy = Goblin()
    print_player_enemy_info(player, enemy, defeated_enemies=[])
    out = capsys.readouterr().out
    assert "Información oculta" in out


def test_print_player_enemy_info_shows_stats_of_defeated_enemy(player, capsys):
    enemy = Goblin()
    print_player_enemy_info(player, enemy, defeated_enemies=[enemy.name])
    out = capsys.readouterr().out
    assert f"Vida: {enemy.stats.health}/{enemy.stats.max_health}" in out


def test_print_player_enemy_info_pairs_related_stats_on_one_line(player, capsys):
    enemy = Goblin()
    print_player_enemy_info(player, enemy, defeated_enemies=[enemy.name])
    out = capsys.readouterr().out
    # Contraparte / relación en la misma línea, para el jugador y el enemigo.
    assert "Armadura:" in out and "| Resistencia Mágica:" in out
    assert "Precisión:" in out and "| Evasión:" in out
    # El daño crítico del jugador y el crítico del enemigo ahora se muestran.
    assert out.count("Daño Crítico:") == 2
    # Como bonus (+50%: x1.5 es "50% más daño"), no como total (150%) ni
    # como multiplicador (x1.50).
    assert "x1." not in out
    assert f"Daño Crítico: +{(player.get_total_crit_damage() - 1) * 100:.0f}%" in out
    assert f"Daño Crítico: +{(enemy.stats.crit_damage - 1) * 100:.0f}%" in out


def test_print_player_enemy_info_shows_magic_attack_for_arcanist(capsys):
    from valeterna.characters.classes import CharClass, starting_stats
    from valeterna.characters.player import Player

    arc = Player("A", starting_stats(CharClass.ARCANISTA), char_class=CharClass.ARCANISTA)
    print_player_enemy_info(arc, Goblin(), defeated_enemies=[])
    out = capsys.readouterr().out
    assert "Ataque mágico:" in out
    assert "Poder Mágico:" in out


def test_print_bestiary_entry_includes_kill_count_and_gold(capsys):
    enemy = Goblin()
    print_bestiary_entry(enemy, kill_count=7)
    out = capsys.readouterr().out
    assert "Veces derrotado: 7" in out
    assert f"{enemy.gold_min}-{enemy.gold_max}" in out


def test_print_bestiary_entry_shows_elemental_weakness(capsys):
    print_bestiary_entry(Troll(), kill_count=5)
    out = capsys.readouterr().out
    assert "Débil a" in out
    assert "Fuego" in out
