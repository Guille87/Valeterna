from valeterna import i18n
from valeterna.items.factory import item_kind_label
from valeterna.ui import console

_HIDDEN = "???"


def _p(text: str, key: str) -> None:
    """Imprime una línea de estadística sangrada y coloreada por concepto."""
    print(f"  {console.stat_line(text, key)}")


def print_player_enemy_info(player, enemy, defeated_enemies: list) -> None:
    """Muestra estadísticas detalladas del jugador y del enemigo. Si el enemigo
    no se ha derrotado todavía, sus valores salen como `???` (igual que la barra
    de vida en combate)."""
    print(f"\nInformación de {console.colorize(player.name, console.Fore.GREEN)}:")
    _p(f"Nivel: {player.level}", "nivel")
    _p(f"Vida: {player.stats.health}/{player.stats.max_health}", "vida")

    if player.is_magical_attacker():
        atk_min, atk_max = player.get_magic_attack_range()
        _p(f"Ataque mágico: {atk_min}-{atk_max} | Poder Mágico: {player.get_total_magic_power()}", "ataque")
    else:
        atk_min, atk_max = player.get_attack_range()
        _p(f"Ataque: {atk_min}-{atk_max}", "ataque")
    _p(f"Armadura: {player.get_total_armor()} | Resistencia Mágica: {player.get_total_magic_resist()}", "armadura")
    _p(
        f"Prob. Crítico: {player.get_total_crit_chance() * 100:.0f}% | "
        f"Daño Crítico: +{(player.get_total_crit_damage() - 1) * 100:.0f}%",
        "critico",
    )
    _p(f"Velocidad: {player.get_total_speed()}", "velocidad")
    _p(f"Precisión: {player.get_total_precision()} | Evasión: {player.get_total_evasion()}", "precision")
    _p(
        f"Penetración de Armadura: {player.get_total_armor_penetration()} | "
        f"Penetración Mágica: {player.get_total_magic_penetration()}",
        "penetracion",
    )
    if player.get_total_regen():
        _p(f"Regeneración: {player.get_total_regen()} HP/turno", "regen")
    print()

    revealed = enemy.name in defeated_enemies
    print(f"Información de {console.colorize(enemy.name, console.Fore.RED)}:")
    if not revealed:
        print(f"  {console.colorize('??? [Información oculta hasta derrotarlo]', console.Fore.BLACK, bright=True)}")

    def ev(value) -> str:
        return str(value) if revealed else _HIDDEN

    _p(f"Vida: {ev(enemy.stats.health)}/{ev(enemy.stats.max_health)}", "vida")
    _p(f"Ataque: {ev(enemy.stats.min_atk)}-{ev(enemy.stats.max_atk)}", "ataque")
    _p(f"Armadura: {ev(enemy.stats.armor)} | Resistencia Mágica: {ev(enemy.stats.magic_resist)}", "armadura")
    _p(
        f"Prob. Crítico: {f'{enemy.stats.crit_chance * 100:.0f}%' if revealed else _HIDDEN} | "
        f"Daño Crítico: {f'+{(enemy.stats.crit_damage - 1) * 100:.0f}%' if revealed else _HIDDEN}",
        "critico",
    )
    _p(f"Velocidad: {ev(enemy.stats.speed)}", "velocidad")
    _p(f"Precisión: {ev(enemy.stats.precision)} | Evasión: {ev(enemy.stats.evasion)}", "precision")
    _p(
        f"Penetración de Armadura: {ev(enemy.stats.armor_penetration)} | "
        f"Penetración Mágica: {ev(enemy.stats.magic_penetration)}",
        "penetracion",
    )
    if revealed and enemy.stats.regen:
        _p(f"Regeneración: {enemy.stats.regen} HP/turno", "regen")

    print("\n" + "=" * 60)


# Escalones del Bestiario (GDD §7.2): con cuántas derrotas se revela cada bloque.
BESTIARY_BASIC = 1  # vida, ataque, oro, descripción, elementos que inflige
BESTIARY_COMBAT = 3  # resto de estadísticas y habilidad característica
BESTIARY_AFFINITY = 5  # afinidades elementales y estados
BESTIARY_DROPS = 10  # tabla de drops completa


def _elements(names) -> str:
    # Cada elemento en su propio color (fuego rojo, veneno verde, rayo
    # amarillo, hielo azul...).
    return ", ".join(console.colorize(e.capitalize(), console.element_color(e), bright=True) for e in sorted(names))


def _statuses(names) -> str:
    return ", ".join(console.tint_status(i18n.t(f"status.{n}")) for n in sorted(names))


def print_bestiary_entry(enemy, kill_count: int = 0) -> None:
    """Ficha de un enemigo ya derrotado, que se va completando según las veces que
    lo has derrotado (GDD §7.2): 1 → datos básicos, 3 → estadísticas de combate y
    habilidad, 5 → afinidades y estados, 10 → tabla de drops."""
    cls = type(enemy)
    print(f"\n{console.colorize(f'--- {enemy.name} ---', console.Fore.RED, bright=True)}")
    _p(f"Veces derrotado: {kill_count}", "kills")
    if cls.DESCRIPTION:
        print(f"  {console.colorize(cls.DESCRIPTION, console.Fore.WHITE, tint=False)}")
    _p(f"Vida máxima: {enemy.stats.max_health}", "vida")
    _p(f"Ataque: {enemy.stats.min_atk}-{enemy.stats.max_atk}", "ataque")
    if cls.ELEMENTS_DEALT:
        print(f"  Sus ataques infligen: {_elements(cls.ELEMENTS_DEALT)}")
    _p(f"Oro al derrotarlo: {enemy.gold_min}-{enemy.gold_max}", "oro")

    if kill_count >= BESTIARY_COMBAT:
        _p(f"Armadura: {enemy.stats.armor} | Resistencia Mágica: {enemy.stats.magic_resist}", "armadura")
        _p(f"Velocidad: {enemy.stats.speed}", "velocidad")
        _p(f"Precisión: {enemy.stats.precision} | Evasión: {enemy.stats.evasion}", "precision")
        _p(
            f"Prob. Crítico: {enemy.stats.crit_chance * 100:.0f}% | "
            f"Daño Crítico: +{(enemy.stats.crit_damage - 1) * 100:.0f}%",
            "critico",
        )
        _p(
            f"Penetración de Armadura: {enemy.stats.armor_penetration} | "
            f"Penetración Mágica: {enemy.stats.magic_penetration}",
            "penetracion",
        )
        if enemy.stats.regen:
            _p(f"Regeneración: {enemy.stats.regen} HP/turno", "regen")
        if cls.SIGNATURE:
            print(f"  Habilidad {cls.SIGNATURE}")

    if kill_count >= BESTIARY_AFFINITY:
        if cls.WEAKNESSES:
            print(f"  Débil a: {_elements(cls.WEAKNESSES)}")
        if cls.RESISTANCES:
            print(f"  Resiste: {_elements(cls.RESISTANCES)}")
        if cls.IMMUNE_ELEMENTS:
            print(f"  Inmune a: {_elements(cls.IMMUNE_ELEMENTS)}")
        if cls.INFLICTS:
            print(f"  Puede infligirte: {_statuses(cls.INFLICTS)}")
        if cls.IMMUNE_STATUSES:
            print(f"  Inmune a los estados: {_statuses(cls.IMMUNE_STATUSES)}")

    if kill_count >= BESTIARY_DROPS:
        print("  Botín posible:")
        for item, chance in enemy.drop_table():
            print(f"    - {item.name} ({item_kind_label(item)}): {chance * 100:.0f}%")

    next_tier = next((t for t in (BESTIARY_COMBAT, BESTIARY_AFFINITY, BESTIARY_DROPS) if kill_count < t), None)
    if next_tier is not None:
        print(
            f"  {console.colorize(f'(Derrótalo {next_tier} veces para descubrir más.)', console.Fore.BLACK, bright=True)}"
        )
    print("=" * 60)


_STATUS_SHORT = {"fractura_magica": "fractura", "regeneración": "regen"}


def _status_badge(combatant) -> str:
    """`  [quemado 2 · veneno 1]` con los estados activos y sus turnos restantes."""
    effects = getattr(combatant, "status_effects", None)
    if not effects:
        return ""
    parts = [console.tint_status(f"{_STATUS_SHORT.get(e['name'], e['name'])} {e['duration']}") for e in effects]
    return "  [" + " · ".join(parts) + "]"


def _bar(current: int, maximum: int, color, hidden: bool = False) -> str:
    if hidden:
        return f"|{'?' * 20}| ??/?? HP"
    percent = max(0, min(current / maximum, 1))
    filled = int(20 * percent)
    bar = "#" * filled + "-" * (20 - filled)
    return f"|{console.colorize(bar, color)}| {current}/{maximum} HP"


def _bar_line(
    name: str, current: int, maximum: int, name_color, bar_color, *, width: int, hidden=False, badge=""
) -> str:
    return f"{console.colorize(name.ljust(width), name_color)}: {_bar(current, maximum, bar_color, hidden)}{badge}"


def print_combatant_bar(combatant, *, is_player: bool) -> None:
    """Una sola línea de vida (con estados). Para mostrar la salud tras un tick
    de veneno/quemadura sin repetir todo el resumen del combate."""
    name_color = console.Fore.CYAN if is_player else console.Fore.LIGHTRED_EX
    bar_color = console.Fore.GREEN if is_player else console.Fore.RED
    print(
        _bar_line(
            combatant.name,
            combatant.stats.health,
            combatant.stats.max_health,
            name_color,
            bar_color,
            width=len(combatant.name),
            badge=_status_badge(combatant),
        )
    )


def print_status(player, enemy, defeated_enemies: list) -> None:
    """Muestra las barras de salud gráficas de ambos combatientes."""
    width = max(len(player.name), len(enemy.name))
    print(
        _bar_line(
            player.name,
            player.stats.health,
            player.stats.max_health,
            console.Fore.CYAN,
            console.Fore.GREEN,
            width=width,
            badge=_status_badge(player),
        )
    )
    # Los estados del enemigo solo se ven si ya lo has derrotado antes.
    is_hidden = enemy.name not in defeated_enemies
    print(
        _bar_line(
            enemy.name,
            enemy.stats.health,
            enemy.stats.max_health,
            console.Fore.LIGHTRED_EX,
            console.Fore.RED,
            width=width,
            hidden=is_hidden,
            badge="" if is_hidden else _status_badge(enemy),
        )
    )
    print("=" * 60)
