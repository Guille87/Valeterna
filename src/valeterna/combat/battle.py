import random
import time
from typing import TYPE_CHECKING

from valeterna import i18n
from valeterna.audio.resource_manager import ResourceManager
from valeterna.characters.enemies.enemy_base import status_label
from valeterna.characters.stats import resolve_hit
from valeterna.combat.elements import element_al, element_phrase, is_magical_element
from valeterna.ui import console
from valeterna.ui.formatting import print_combatant_bar, print_player_enemy_info, print_status
from valeterna.ui.keyboard import key_pressed

if TYPE_CHECKING:
    from valeterna.characters.enemies.enemy_base import Enemy
    from valeterna.characters.player import Player

# Mapa de progresión: Al derrotar a la LLAVE, se desbloquea el VALOR.
# Orden de tiers acordado con el usuario (ver TODO.md): los enemigos nuevos se
# van insertando en el hueco que les corresponde según su potencia relativa a
# los que ya existían, no necesariamente al final de la cadena.
ENEMY_PROGRESSION = {
    "Goblin": "Rata Gigante",
    "Rata Gigante": "Goblin Montaraz",
    "Goblin Montaraz": "Huargo",
    "Huargo": "Chamán Goblin",
    "Chamán Goblin": "Esqueleto",
    "Esqueleto": "Bandido",
    "Bandido": "Salteador",
    "Salteador": "Ogro del Yermo",
    "Ogro del Yermo": "El Carnicero",
    "El Carnicero": "Orco",  # guardián de Los Yermos: abre el Bosque
    "Orco": "Espíritu Vengativo",
    "Espíritu Vengativo": "Troll",
    "Troll": "Gárgola",
    "Gárgola": "Gólem de Piedra",
    "Gólem de Piedra": "Mago",
    "Mago": "Nigromante",
    "Nigromante": "Ángel Caído",
    "Ángel Caído": "Demonio",
    "Demonio": "Dragón",
    "Dragón": None,  # Jefe final de la cadena
}

# Umbral de la barra ATB: cuando el "gauge" de un combatiente llega aquí, actúa
# y se le resta el umbral (el sobrante se conserva, no se pierde). Con esto la
# velocidad no decide solo quién va primero, sino con qué frecuencia actúa cada
# uno (estilo Final Fantasy X), permitiendo que el más rápido actúe varias
# veces antes de que el más lento llegue a su primer turno.
ATB_THRESHOLD = 100


def check_for_interrupt() -> bool:
    """Retorna True si el usuario ha pulsado 'q' o 'Q'."""
    return key_pressed() == "q"


def _turn_header(turn_no: int, name: str, extra: str = "") -> str:
    """Cabecera tenue con el número de acción global y quién actúa (con su clase,
    para el jugador)."""
    suffix = f" ({extra})" if extra else ""
    return console.colorize(f"\n── Turno {turn_no} · {name}{suffix} ──", console.Fore.LIGHTBLACK_EX, bright=True)


_MAX_CHAIN_BATTLES = 20


def _ask_chain_count() -> int:
    """Pregunta cuántas peleas seguidas quiere el jugador al activar la
    auto-batalla contra un enemigo ya derrotado. Enter / algo no numérico -> 1;
    por encima del máximo, se avisa y se recorta."""
    raw = console.ask(f"¿Cuántas peleas seguidas? (1-{_MAX_CHAIN_BATTLES}, Enter = 1): ").strip()
    if not raw:
        return 1
    if not raw.isdigit():
        console.warning("Eso no es un número; se hará una sola pelea.")
        return 1
    n = int(raw)
    if n > _MAX_CHAIN_BATTLES:
        console.warning(f"El máximo son {_MAX_CHAIN_BATTLES} peleas seguidas.")
        return _MAX_CHAIN_BATTLES
    return max(1, n)


def initiate_battle(player, enemy, defeated_enemies: list, unlocked_enemies: list, *, enemy_factory=None) -> str:
    """Punto de entrada principal para cualquier combate.

    Si al activar la auto-batalla (o el turbo) contra un enemigo ya derrotado el
    jugador pide varias peleas seguidas, aquí se encadenan: cada pelea es como
    siempre (botín, oro, XP, curación) y la siguiente arranca sola en el mismo
    modo. `enemy_factory` (una función que crea una instancia nueva del enemigo)
    es necesaria para poder encadenar; sin ella solo se juega una pelea.

    Devuelve el desenlace de la última pelea: `"victory"`, `"defeat"`, `"fled"`
    o `"cancelled"` (el jugador pulsó 'Q' y terminó a mano sin volver a auto)."""
    rm = ResourceManager()
    rm.enter_battle(enemy.name)
    player.in_combat = True

    # Estado de la cadena, compartido con _run_player_turn: cuando el jugador
    # elige auto/turbo se rellenan "count" y "mode"; "mode" puede cambiar a mitad
    # (p. ej. pasar de auto a turbo tras pulsar 'Q').
    chain = {"factory": enemy_factory, "chosen": False, "count": 1, "mode": False}

    # Instantánea para el resumen de botín de la cadena (oro/XP/nivel/objetos).
    chain_start = {
        "gold": player.inventory.gold,
        "xp": player.experience,
        "level": player.level,
        "items": dict(player.inventory.quantities),
    }

    fight_index = 1
    current_enemy = enemy
    outcome = "victory"
    while True:
        if fight_index > 1:
            print(
                console.colorize(
                    f"\n=== CADENA DE BATALLA: PELEA {fight_index}/{chain['count']} ===",
                    console.Fore.MAGENTA,
                    bright=True,
                )
            )
        outcome = _run_one_battle(player, current_enemy, defeated_enemies, unlocked_enemies, chain, fight_index)
        if outcome != "victory" or fight_index >= chain["count"]:
            break
        fight_index += 1
        current_enemy = chain["factory"]()

    player.in_combat = False
    rm.exit_battle()

    if chain["count"] > 1:
        if outcome == "victory":
            console.success(f"🔗 Cadena completada: {chain['count']}/{chain['count']} peleas.")
        else:
            done = fight_index - 1 if outcome in ("defeat", "fled") else fight_index
            motivo = {
                "defeat": "Has caído en combate",
                "fled": "Has huido",
                "cancelled": "Has salido del modo automático",
            }.get(outcome, "Cadena interrumpida")
            console.warning(f"🔗 {motivo}. Cadena interrumpida ({done}/{chain['count']} peleas completadas).")
        # Resumen de todo lo conseguido en la cadena (en 20 peleas es fácil
        # perder la cuenta) y una única pausa al final, gane o pierda.
        _print_chain_loot(player, chain_start)
        console.ask(f"\n{console.colorize('Presiona Enter para continuar...', console.Fore.YELLOW)}")
        return outcome

    # Pelea única: pausa salvo tras una victoria limpia en turbo (farmeo) y
    # salvo tras una derrota (ya pausó _handle_defeat).
    clean_turbo_win = outcome == "victory" and chain["mode"] == "turbo"
    if outcome in ("victory", "cancelled", "fled") and not clean_turbo_win:
        console.ask(f"\n{console.colorize('Presiona Enter para continuar...', console.Fore.YELLOW)}")

    return outcome


def _print_chain_loot(player, start: dict) -> None:
    """Resumen del botín acumulado en una cadena de peleas: oro, XP, niveles y
    objetos nuevos (por diferencia contra la instantánea del inicio)."""
    from valeterna.items.equipment import Armor, Weapon
    from valeterna.items.factory import item_kind_label
    from valeterna.items.materials import Material
    from valeterna.items.potions.potion_base import Potion

    gold_delta = player.inventory.gold - start["gold"]
    xp_delta = player.experience - start["xp"]
    levels = player.level - start["level"]

    gained = {
        name: qty - start["items"].get(name, 0)
        for name, qty in player.inventory.quantities.items()
        if qty - start["items"].get(name, 0) > 0
    }

    print(console.colorize("\n--- BOTÍN DE LA CADENA ---", console.Fore.CYAN, bright=True))
    gold_sign = "+" if gold_delta >= 0 else ""
    print(console.stat_line(f"Oro: {gold_sign}{gold_delta}", "oro"))
    xp_line = f"XP: +{xp_delta}"
    if levels > 0:
        xp_line += f"  (subes {levels} nivel{'es' if levels > 1 else ''}: {start['level']} → {player.level})"
    print(console.stat_line(xp_line, "xp"))

    if not gained:
        print("Objetos: ninguno")
        return

    item_by_name = {it.name: it for it in player.inventory.items}

    def _color(name: str) -> str:
        item = item_by_name.get(name)
        if isinstance(item, Weapon):
            return console.colorize(name, console.element_color(item.element))
        if isinstance(item, Armor):
            return console.colorize(name, console.Fore.BLUE, bright=True)
        if isinstance(item, Potion):
            return console.colorize(name, console.Fore.GREEN)
        if isinstance(item, Material):
            return console.colorize(name, console.Fore.LIGHTBLACK_EX)
        return name

    print("Objetos:")
    for name, qty in gained.items():
        suffix = f" x{qty}" if qty > 1 else ""
        label = item_kind_label(item_by_name[name]) if name in item_by_name else "objeto"
        kind = console.colorize(f"({label})", console.Fore.LIGHTBLACK_EX)
        print(f"  {_color(name)}{suffix} {kind}")


def _seen_flag(enemy) -> str:
    return f"vio_a_{enemy.name}"


def _defeat_flag(enemy) -> str:
    return f"perdio_contra_{enemy.name}"


def _announce_encounter(player, enemy) -> None:
    """Frase de encuentro al toparte con un enemigo (v0.14.x, GDD §8.1
    follow-up, feedback del usuario: estilo "un Pokémon salvaje apareció",
    no es un árbol de diálogo como `world/npc.py` — solo una línea de sabor,
    sin ramas ni respuestas. Sale tanto desde Explorar como desde Cazar: no
    describe cómo lo encontraste, describe enfrentarte a ÉL.

    1ª vez que ves a este enemigo (`ENCOUNTER_LINE`): siempre, para
    cualquier tipo. Desde la 2ª vez, solo élite/guardián dicen algo más, y
    solo si el jugador ya perdió contra él alguna vez (`_defeat_flag`,
    puesto por `_handle_defeat`) — una `TAUNT_LINES` al azar en vez de
    repetir la misma frase de siempre."""
    banderas = player.mundo["banderas"]
    seen_flag = _seen_flag(enemy)

    if seen_flag not in banderas:
        banderas.add(seen_flag)
        if enemy.ENCOUNTER_LINE:
            dramatic = enemy.ENCOUNTER_KIND != "normal"
            color = console.Fore.RED if dramatic else console.Fore.LIGHTBLACK_EX
            print(console.colorize(enemy.ENCOUNTER_LINE, color, bright=dramatic, tint=False))
        return

    if enemy.ENCOUNTER_KIND != "normal" and enemy.TAUNT_LINES and _defeat_flag(enemy) in banderas:
        print(console.colorize(random.choice(enemy.TAUNT_LINES), console.Fore.RED, bright=True, tint=False))


def _run_one_battle(
    player, enemy, defeated_enemies: list, unlocked_enemies: list, chain: dict, fight_index: int
) -> str:
    """Una sola pelea completa. `chain` guía el modo automático de arranque (en
    la 2ª pelea de una cadena en adelante) y recoge la elección del jugador si
    activa la auto-batalla aquí. Devuelve `"victory"` / `"defeat"` / `"fled"` /
    `"cancelled"`."""
    # En la 2ª pelea de una cadena en adelante arrancamos ya en el modo elegido.
    start_auto: bool | str = chain["mode"] if fight_index > 1 else False

    # Frase de encuentro (v0.14.x, GDD §8.1 follow-up): antes de que empiece
    # la batalla "de verdad", igual que el resto del sabor de esta pantalla se
    # omite en Turbo (farmeo).
    if start_auto != "turbo":
        _announce_encounter(player, enemy)

    print("=" * 60)
    print(f"{console.colorize(f'¡Ha comenzado la batalla contra {enemy.name}!', console.Fore.WHITE, bright=True)}")
    rm = ResourceManager()
    # Vida justo al entrar en combate: si el jugador huye, solo debe poder
    # recuperar parte de lo que ha perdido en ESTA pelea.
    health_before_battle = player.stats.health

    # Ficha de ambos combatientes al empezar, ANTES de la posible emboscada (para
    # ver el enfrentamiento antes de que el enemigo pegue primero). En turbo se
    # omite (farmeo).
    if start_auto != "turbo":
        print_player_enemy_info(player, enemy, defeated_enemies)

    # --- LÓGICA DE EMBOSCADA (Ataque previo) ---
    if hasattr(enemy, "check_ambush"):
        if enemy.check_ambush(player, defeated_enemies):
            print_status(player, enemy, defeated_enemies)

        if not player.is_alive():
            # En una cadena la pausa (y el resumen) van una sola vez al final.
            _handle_defeat(player, enemy, pause=chain["count"] == 1)
            _restore_player(player, {"atk": (player.stats.min_atk, player.stats.max_atk), "armor": player.stats.armor})
            return "defeat"

    # Pasiva "Sintonía" (Arcanista): elige el elemento de tu ataque este combate.
    if not start_auto:
        _prompt_battle_element(player)

    # Quién tiene la iniciativa: no es "quién tiene más velocidad" sin más,
    # sino quién llega antes al umbral ATB en la carrera real de gauges de
    # más abajo — con velocidades parecidas ambos pueden cruzar el umbral en
    # el mismo "tick", y ahí el turno del jugador se resuelve siempre primero
    # (para que un enemigo más rápido nunca pueda interrumpir una huida). El
    # mensaje anterior solo comparaba velocidades y podía anunciar al enemigo
    # aunque el jugador fuese a actuar primero de todos modos (playtest fix).
    # No se muestran los números de velocidad: antes del primer combate contra
    # un enemigo esa cifra es información que el Bestiario todavía redacta
    # como "???" (feedback del usuario) — el mensaje solo dice quién empieza.
    if start_auto != "turbo":
        pv, ev = player.get_total_speed(), enemy.stats.speed
        ticks_jugador = -(-ATB_THRESHOLD // max(1, pv))  # división entera hacia arriba
        ticks_enemigo = -(-ATB_THRESHOLD // max(1, ev))
        primero = player.name if ticks_jugador <= ticks_enemigo else enemy.name
        print(
            console.colorize(
                f"⚡ {primero} tiene la iniciativa.",
                console.Fore.LIGHTBLACK_EX,
                bright=True,
            )
        )

    snapshot = {"atk": (player.stats.min_atk, player.stats.max_atk), "armor": player.stats.armor}
    cooldowns: dict[str, int] = {}  # enfriamiento de habilidades, solo dura este combate
    turn_no = 0  # contador global de acciones (jugador o enemigo)

    is_auto: bool | str = start_auto
    if start_auto:
        modo = "TURBO (sin pausas)" if start_auto == "turbo" else "ACTIVADO"
        print(console.colorize(f">>> MODO AUTO: {modo}. (Pulsa 'Q' para detener)", console.Fore.CYAN))
    auto_cancelled = False
    player_won = False
    player_fled = False
    player_defeated = False
    gauge_player = 0.0
    gauge_enemy = 0.0
    enemy_acted = True  # el primer turno del jugador no cuenta como "repetido"
    player_acted = True  # el primer turno del enemigo no cuenta como "repetido"
    while player.is_alive() and enemy.is_alive():
        rm.update()

        # --- BARRA ATB: avanzamos el "reloj" hasta que alguien esté listo ---
        while gauge_player < ATB_THRESHOLD and gauge_enemy < ATB_THRESHOLD:
            gauge_player += player.get_total_speed()
            gauge_enemy += enemy.stats.speed

        # El turno del jugador (y una posible huida) se resuelve siempre antes que
        # el del enemigo si ambos gauges están listos en el mismo "tick".
        if gauge_player >= ATB_THRESHOLD:
            gauge_player -= ATB_THRESHOLD
            turn_no += 1
            was_auto = bool(is_auto)
            signal, is_auto = _run_player_turn(
                player,
                enemy,
                defeated_enemies,
                is_auto,
                repeated=not enemy_acted,
                chain=chain,
                cooldowns=cooldowns,
                turn_no=turn_no,
            )
            if was_auto and not is_auto:
                auto_cancelled = True  # pulsó 'Q'; si vuelve a activar auto se corrige abajo
            enemy_acted = False
            player_acted = True
            if signal == "huir":
                player_fled = True
                break

        if not enemy.is_alive():
            player_won = True
            new_atk, new_armor = _handle_victory(player, enemy, defeated_enemies, unlocked_enemies)
            if player.just_leveled_up:
                snapshot["atk"] = new_atk
                snapshot["armor"] = new_armor
            break

        # --- TURNO DEL ENEMIGO (solo si su gauge también está lista) ---
        if player.is_alive() and gauge_enemy >= ATB_THRESHOLD:
            gauge_enemy -= ATB_THRESHOLD
            turn_no += 1
            _run_enemy_turn(
                player, enemy, defeated_enemies, turbo=is_auto == "turbo", turn_no=turn_no, repeated=not player_acted
            )
            enemy_acted = True
            player_acted = False
            _try_represalia(player, enemy, defeated_enemies)
            player.took_physical_hit = False

        # El enemigo pudo morir por veneno/quemadura al empezar su turno.
        if not enemy.is_alive():
            player_won = True
            new_atk, new_armor = _handle_victory(player, enemy, defeated_enemies, unlocked_enemies)
            if player.just_leveled_up:
                snapshot["atk"] = new_atk
                snapshot["armor"] = new_armor
            break

        if not player.is_alive():
            _handle_defeat(player, enemy, pause=chain["count"] == 1)  # cura del todo -> de ahí el flag
            player_defeated = True
            break

    if player_fled:
        _restore_player(player, snapshot, max_recovery=health_before_battle - player.stats.health)
    else:
        _restore_player(player, snapshot)

    if player_defeated:
        return "defeat"
    if player_fled:
        return "fled"
    # "cancelled" solo si pulsó 'Q' y NO volvió a activar la auto-batalla.
    if auto_cancelled and not is_auto:
        return "cancelled"
    return "victory" if player_won else "fled"


def _player_menu(player, enemy, defeated_enemies: list, immobilized: bool = False) -> str:
    """Maneja la interfaz de usuario durante el combate. Si `immobilized`
    (parálisis/congelación), no se ofrece "Defender" ni "Habilidades" y "Atacar"
    pierde el turno, pero sí se puede usar un objeto o intentar huir."""
    while True:
        # Opciones numeradas dinámicamente: (etiqueta, token que devuelve).
        options: list[tuple[str, str]] = [
            ("Atacar (no puedes moverte)" if immobilized else "Atacar", "atacar"),
        ]
        if not immobilized:
            if player.get_equipped_active_skills():
                options.append(("Habilidades", "habilidades"))
            options.append(("Defender", "defender"))
        options.append(("Objetos", "objetos"))
        options.append(("Huir", "huir"))
        options.append(("Info", "info"))
        if enemy.name in defeated_enemies:
            options.append(("Auto-Batalla", "auto"))
            options.append(("Auto-Batalla Turbo", "turbo"))

        print(" | ".join(f"{i}. {label}" for i, (label, _) in enumerate(options, 1)))
        choice = console.ask("Selección: ").strip()
        if not choice.isdigit() or not (1 <= int(choice) <= len(options)):
            console.error("Opción no válida.")
            continue

        token = options[int(choice) - 1][1]
        if token == "objetos":
            if player.inventory.equip_menu():  # True = se usó un objeto
                return "objeto_usado"
            continue
        if token == "info":
            print_player_enemy_info(player, enemy, defeated_enemies)
            continue
        return token


def _attempt_flee(player, enemy, chance_mult: float = 1.0) -> bool:
    """Probabilidad de huir con éxito.

    Si el jugador es igual o más rápido que el enemigo, la huida es siempre
    segura (100%). Por debajo de eso, la probabilidad baja junto con la
    velocidad relativa, pero nunca llega a 0. `chance_mult` la reduce (0.5 si el
    jugador está inmovilizado por parálisis/congelación).
    """
    player_speed = max(1, player.get_total_speed())
    enemy_speed = max(1, enemy.stats.speed)
    flee_chance = min(1.0, player_speed / enemy_speed) * chance_mult
    return random.random() < flee_chance


def _run_player_turn(
    player,
    enemy,
    defeated_enemies: list,
    is_auto,
    repeated: bool = False,
    chain: dict | None = None,
    cooldowns=None,
    turn_no: int = 0,
):
    """Ejecuta el turno del jugador cuando su gauge ATB está lista.

    `is_auto` es `False`, `"auto"` (auto normal, con pausas) o `"turbo"` (auto
    sin pausas, para farmear). `repeated` = el jugador vuelve a actuar sin que el
    enemigo haya actuado por el medio (es más rápido). `chain` (si se pasa) recibe
    la elección del jugador al activar la auto-batalla: la primera vez se le
    pregunta cuántas peleas seguidas quiere; el modo (`"auto"`/`"turbo"`) se
    actualiza siempre, para poder cambiar de uno a otro a mitad de una cadena.
    Devuelve `(señal, is_auto actualizado)`; señal es `"huir"` o `"ok"`.
    """
    if turn_no:
        print(_turn_header(turn_no, player.name, getattr(player, "class_name", "")))

    # --- INICIO DE TURNO (Procesar veneno, quemaduras, parálisis) ---
    # La postura defensiva del turno anterior solo cubre hasta que al jugador le
    # vuelve a tocar: al empezar su turno se limpia.
    player.defending = False
    hp_before = player.stats.health
    can_act = player.on_turn_start()
    turn_consumed = False

    # Enfriamiento de habilidades: baja 1 en cada turno del jugador.
    cooldowns = cooldowns if cooldowns is not None else {}
    for sid in list(cooldowns):
        cooldowns[sid] = max(0, cooldowns[sid] - 1)

    # Si el veneno/quemadura le hizo daño, una línea con su vida (barra +
    # estados) para que sepa con cuánta se queda antes de decidir.
    if player.is_alive() and player.stats.health != hp_before:
        print_combatant_bar(player, is_player=True)

    if repeated and not is_auto and player.is_alive():
        print(console.colorize(f"⏩ Eres más rápido: actúas de nuevo antes que {enemy.name}.", console.Fore.CYAN))

    # --- COMPROBAR CANCELACIÓN DE AUTO ---
    if is_auto and check_for_interrupt():
        was_turbo = is_auto == "turbo"
        is_auto = False
        console.warning("\n🛑 Auto-batalla detenida. Vuelves a controlar el combate.")
        if not was_turbo:
            time.sleep(1)  # Pausa para que el usuario lo vea

    action = None
    if player.is_alive():  # El veneno podría haberlo matado en on_turn_start
        if not is_auto:
            action = "_menu"
            while action == "_menu":
                action = _player_menu(player, enemy, defeated_enemies, immobilized=not can_act)
                if action == "habilidades":
                    skill = _choose_skill(player, cooldowns)
                    if skill is None:
                        action = "_menu"  # volver al menú de combate
                        continue
                    _execute_skill(player, enemy, skill, defeated_enemies)
                    cooldowns[skill.id] = skill.cooldown
                    turn_consumed = True

            if action == "huir":
                # Inmovilizado, la probabilidad de huir baja a la mitad.
                if _attempt_flee(player, enemy, chance_mult=1.0 if can_act else 0.5):
                    console.warning("Has huido del combate...")
                    return "huir", is_auto
                console.error(f"¡No has podido escapar de {enemy.name}!")
                turn_consumed = True

            if action in ("auto", "turbo"):
                is_auto = action
                # Cadena de peleas: se pregunta la primera vez que se activa la
                # auto-batalla; el modo se actualiza siempre (permite cambiar de
                # auto a turbo o viceversa a mitad de una cadena).
                if chain is not None:
                    if chain["factory"] and not chain["chosen"]:
                        chain["chosen"] = True
                        chain["count"] = _ask_chain_count()
                    chain["mode"] = action
                modo = "TURBO (sin pausas)" if action == "turbo" else "ACTIVADO"
                print(console.colorize(f">>> MODO AUTO: {modo}. (Pulsa 'Q' para detener)", console.Fore.CYAN))

            if action == "defender":
                player.defending = True
                turn_consumed = True
                print(
                    console.colorize(
                        f"{player.name} adopta una postura defensiva: el daño recibido hasta su "
                        "siguiente turno se reduce a la mitad.",
                        console.Fore.CYAN,
                    )
                )

            if action == "objeto_usado":
                turn_consumed = True

            if action == "atacar" and not can_act:
                console.warning("Intentas moverte, pero no puedes. Pierdes el turno.")

        # --- ATAQUE DEL JUGADOR (Si puede actuar) ---
        if (is_auto or action == "atacar") and can_act and not turn_consumed:
            # En auto/turbo: usa una activa equipada que esté lista si la hay.
            auto_skill = _pick_auto_skill(player, cooldowns) if is_auto else None
            if auto_skill is not None:
                _execute_skill(player, enemy, auto_skill, defeated_enemies)
                cooldowns[auto_skill.id] = auto_skill.cooldown
            else:
                _execute_turn(player, enemy, defeated_enemies)

    player.on_turn_end()
    return "ok", is_auto


def _prompt_battle_element(player) -> None:
    """Pasiva "Sintonía": deja al jugador elegir el elemento de su ataque para
    este combate. Solo hace algo si tiene la pasiva y aún no lo ha elegido."""
    if player.battle_element or not player.has_passive("sintonia"):
        return
    from valeterna.combat.elements import ELEMENTS

    elements = sorted(ELEMENTS)
    print(console.colorize("\n🎵 Sintonía — elige el elemento de tu ataque este combate:", console.Fore.CYAN))
    print(
        "  "
        + " | ".join(
            f"{console.colorize(f'{i}.', console.Fore.CYAN)} {console.colorize(e.capitalize(), console.element_color(e))}"
            for i, e in enumerate(elements, 1)
        )
    )
    choice = console.ask(f"Elemento (1-{len(elements)}, Enter = ninguno): ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(elements):
        player.battle_element = elements[int(choice) - 1]
        console.success(f"Tu ataque será de {player.battle_element} este combate.")


def _pick_auto_skill(player, cooldowns: dict):
    """Primera habilidad activa equipada disponible (sin enfriamiento) para auto/turbo."""
    for skill in player.get_equipped_active_skills():
        if cooldowns.get(skill.id, 0) <= 0:
            return skill
    return None


def _choose_skill(player, cooldowns: dict):
    """Submenú de habilidades activas equipadas en combate. Devuelve la Skill
    elegida (lista para usar) o `None` si se cancela."""
    actives = player.get_equipped_active_skills()
    if not actives:
        console.error("No tienes habilidades activas equipadas (equípalas en el menú 'Habilidades').")
        return None
    while True:
        print(console.colorize("\n--- HABILIDADES ---", console.Fore.MAGENTA, bright=True))
        for i, skill in enumerate(actives, 1):
            cd = cooldowns.get(skill.id, 0)
            estado = (
                console.colorize("lista", console.Fore.GREEN)
                if cd <= 0
                else console.colorize(
                    f"en enfriamiento: {cd} turno{'s' if cd != 1 else ''}", console.Fore.LIGHTBLACK_EX, bright=True
                )
            )
            print(
                f"{console.colorize(f'{i}.', console.Fore.CYAN)} {console.colorize(skill.name, console.Fore.MAGENTA)} [{estado}]"
            )
            print(f"   {console.tint_status(skill.description)}")
        print(f"{console.colorize(f'{len(actives) + 1}.', console.Fore.CYAN)} Volver")

        choice = console.ask("Elige habilidad: ").strip()
        if not choice.isdigit():
            console.error("Opción no válida.")
            continue
        idx = int(choice) - 1
        if idx == len(actives):
            return None
        if not (0 <= idx < len(actives)):
            console.error("Opción fuera de rango.")
            continue
        skill = actives[idx]
        if cooldowns.get(skill.id, 0) > 0:
            turnos = cooldowns[skill.id]
            console.error(f"{skill.name} todavía está en enfriamiento ({turnos} turno{'s' if turnos != 1 else ''}).")
            continue
        return skill


def _execute_skill(player, enemy, skill, defeated_enemies: list) -> None:
    p = skill.params
    ResourceManager().play_sfx("level_up")

    # Escudo de Maná y otras activas de utilidad: no atacan.
    if p.get("shield_next_hit"):
        player.mana_shield = True
        print(
            console.colorize(
                f"\n🛡️ {player.name} usa {skill.name}: un escudo absorbe el próximo golpe.",
                console.Fore.MAGENTA,
                bright=True,
            )
        )
        return

    print(console.colorize(f"\n✨ {player.name} usa {skill.name}.", console.Fore.MAGENTA, bright=True))
    _execute_turn(player, enemy, defeated_enemies, skill_params=p)


def _try_represalia(player, enemy, defeated_enemies: list) -> None:
    """Pasiva "Represalia" (Guerrero): tras recibir un golpe físico, opción de
    contraatacar de inmediato."""
    if not (player.is_alive() and enemy.is_alive()):
        return
    if not player.took_physical_hit or not player.has_passive("represalia"):
        return
    if random.random() < player.passive_param("represalia", "counter_chance", 0.0):
        print(
            console.colorize(
                "⚔️  ¡Represalia! Contraatacas al recibir el golpe.", console.Fore.LIGHTMAGENTA_EX, bright=True
            )
        )
        _execute_turn(player, enemy, defeated_enemies)


def _run_enemy_turn(
    player, enemy, defeated_enemies: list, turbo: bool = False, turn_no: int = 0, repeated: bool = False
) -> None:
    """Ejecuta el turno del enemigo cuando su gauge ATB está lista. En `turbo`
    solo se saltan las pausas/sleeps; las barras de vida y los avisos se muestran
    igual, para no perder de vista cómo va el combate. `repeated` = el enemigo
    vuelve a actuar sin que el jugador haya actuado por el medio (es más
    rápido) — espejo de la nota "Eres más rápido" del lado del jugador
    (feedback del usuario: la barra ATB podía dar dos turnos seguidos al
    enemigo sin que quedase claro por qué)."""
    if not turbo:
        time.sleep(1)

    # Estados alterados: veneno/quemadura (daño), parálisis/congelación (pierde turno).
    hp_before = enemy.stats.health
    can_act = enemy.on_turn_start()
    if not enemy.is_alive():
        console.info(i18n.t("combat.enemy_succumbs", name=enemy.name))
        enemy.decay_status_effects()
        return
    took_dot = enemy.stats.health != hp_before

    if can_act:
        print(_turn_header(turn_no, enemy.name))
        if repeated:
            print(console.colorize(f"⏩ {enemy.name} es más rápido: actúa de nuevo antes que tú.", console.Fore.CYAN))
        enemy.perform_turn(player)
    enemy.on_turn_end()
    enemy.decay_status_effects()

    # Si el enemigo pierde el turno y no hubo daño por veneno/quemadura, no
    # repetimos las barras de vida: el mensaje de parálisis/congelación basta.
    if can_act or took_dot:
        print_status(player, enemy, defeated_enemies)

    for message in enemy.pop_announcements():
        print(message)

    # Pausa para asimilar el resultado del turno del enemigo antes de que salga
    # el menú (o el siguiente turno). En turbo no.
    if not turbo:
        time.sleep(1)


def _execute_turn(
    attacker: "Player", defender: "Enemy", defeated_enemies: list, *, skill_params: dict | None = None
) -> int | None:
    """Ejecuta un ataque del jugador calculando daño y stats. `skill_params`
    (cuando el ataque viene de una habilidad activa) puede forzar acierto/crítico,
    multiplicar el daño, hacerlo mágico, perforar la resistencia mágica o aplicar
    un estado extra. Devuelve el daño final, o `None` si el golpe falló."""
    from valeterna.characters.player import Player

    p = skill_params or {}

    if isinstance(attacker, Player):
        rm = ResourceManager()
        # Elegimos al azar entre los nombres en AUDIO_ASSETS
        sonido_ataque = random.choice(["hit", "slash"])
        rm.play_sfx(sonido_ataque)

    # Verificación de seguridad: si attacker es una lista, tenemos un problema de lógica previo
    if isinstance(attacker, list):
        console.error("Error Interno: El atacante es una lista, no un objeto.")
        return

    # Tirada de acierto (precisión del atacante vs evasión del defensor):
    # un fallo no llega a tocar armadura ni elementos, así que se resuelve
    # antes que cualquier otro cálculo de daño.
    attacker_precision = attacker.get_total_precision() if isinstance(attacker, Player) else attacker.stats.precision
    defender_evasion = defender.get_total_evasion() if isinstance(defender, Player) else defender.stats.evasion
    if not p.get("guaranteed_hit") and not resolve_hit(attacker_precision, defender_evasion):
        # Un ataque nunca "falla" por sí solo (acierto base 100%): si no entra, es
        # porque el defensor lo esquivó con su evasión.
        print(
            f"{console.colorize(attacker.name, console.Fore.GREEN)} ataca, pero "
            f"{console.colorize(defender.name, console.Fore.RED)} lo esquiva."
        )
        if isinstance(attacker, Player):
            print_status(attacker, defender, defeated_enemies)
        else:
            print_status(defender, attacker, defeated_enemies)
        return None

    # Golpe crítico: el jugador suma el bonus de su equipo, los enemigos usan su stat base.
    # Se calcula ANTES del daño base (ver más abajo: una habilidad o un crítico
    # ya no ruedan el dado normal, así que hace falta saber si toca antes de
    # decidir qué base de daño usar).
    attacker_crit_chance = (
        attacker.get_total_crit_chance() if isinstance(attacker, Player) else attacker.stats.crit_chance
    )
    attacker_crit_damage = (
        attacker.get_total_crit_damage() if isinstance(attacker, Player) else attacker.stats.crit_damage
    )
    is_crit = p.get("force_crit", False) or random.random() < attacker_crit_chance

    # Daño base (v0.14.0-c, feedback del usuario): un ataque normal sigue
    # tirando el dado entre `min_atk` y `max_atk` de siempre, pero una
    # habilidad de daño (cualquier llamada con `skill_params`, ya que las
    # habilidades de utilidad como Escudo de Maná vuelven antes de llegar
    # aquí) o un golpe crítico usan siempre el extremo alto del rango en vez
    # de otra tirada — así el jugador tiene la garantía de que una habilidad,
    # o la suerte de un crítico, nunca van a pegar más flojo que un golpe
    # normal con suerte. El multiplicador propio de la habilidad
    # (`damage_mult`) y el del crítico (`crit_damage`) se siguen aplicando
    # encima, igual que antes. Solo afecta al jugador: los enemigos conservan
    # su tirada aleatoria de siempre (cambiarla recalibraría todo el roster).
    is_skill_attack = bool(p)
    if isinstance(attacker, Player) and (is_skill_attack or is_crit):
        _, damage = attacker.get_magic_attack_range() if attacker.is_magical_attacker() else attacker.get_attack_range()
    else:
        damage = attacker.get_attack_damage()
    if p.get("damage_mult"):
        damage = int(damage * p["damage_mult"])

    # Lo mágico/físico es propiedad del ELEMENTO (GDD §5), no de quién lo
    # empuña: cualquier clase con un arma sagrado/oscuridad/arcano golpea
    # mágico (mitigado con resistencia mágica), no solo el Arcanista. El
    # Arcanista además es mágico "por defecto" (su ataque estándar escala con
    # poder mágico, no con el arma) y cae en "arcano" si no lleva ningún
    # elemento equipado. Una habilidad puede forzar el golpe a mágico
    # (`magical`) sin importar el arma.
    element = attacker.get_equipped_element() if isinstance(attacker, Player) else None
    is_magical_attack = (
        (isinstance(attacker, Player) and attacker.is_magical_attacker())
        or p.get("magical", False)
        or is_magical_element(element)
    )
    if isinstance(attacker, Player) and attacker.is_magical_attacker() and not element:
        from valeterna.characters.classes import ARCANIST_DEFAULT_ELEMENT

        element = ARCANIST_DEFAULT_ELEMENT

    if is_crit:
        damage = int(damage * attacker_crit_damage)

    # Afinidad del defensor al elemento (débil / resistente / inmune). Lo
    # comprobamos antes de aplicar el daño para poder mostrar el mensaje
    # correspondiente (take_damage no expone esa info).
    affinity = defender.affinity_for({element}) if element and hasattr(defender, "affinity_for") else 1.0
    is_super_effective = affinity > 1.0
    is_immune_hit = element and affinity == 0.0
    is_resisted_hit = 0.0 < affinity < 1.0

    # Penetración de armadura: solo tiene efecto en ataques físicos (is_magical=False,
    # el único caso que pasa por aquí hoy), reduce la armadura del defensor antes
    # de restar el daño.
    attacker_armor_penetration = (
        attacker.get_total_armor_penetration() if isinstance(attacker, Player) else attacker.stats.armor_penetration
    )
    if is_magical_attack:
        magic_pen = attacker.get_total_magic_penetration() if isinstance(attacker, Player) else 0
        if p.get("pierce_magic_resist"):
            magic_pen += 9999  # ignora por completo la resistencia mágica del enemigo
        final_dmg = defender.take_damage(
            damage,
            defeated_enemies=defeated_enemies,
            element=element,
            is_magical=True,
            magic_penetration=magic_pen,
        )
    else:
        final_dmg = defender.take_damage(
            damage, defeated_enemies=defeated_enemies, element=element, armor_penetration=attacker_armor_penetration
        )

    element_name = i18n.t(f"element.{element}") if element else ""
    if is_super_effective:
        print(
            console.colorize(
                i18n.t(
                    "combat.super_effective",
                    element_phrase=element_phrase(element_name, capitalize=True),
                    name=defender.name,
                ),
                console.Fore.RED,
                bright=True,
            )
        )
    elif is_immune_hit:
        print(
            console.colorize(
                i18n.t("combat.immune_hit", element_al=element_al(element_name), name=defender.name),
                console.Fore.BLUE,
            )
        )
    elif is_resisted_hit:
        print(
            console.colorize(
                i18n.t("combat.resisted_hit", element_al=element_al(element_name), name=defender.name),
                console.Fore.BLUE,
            )
        )

    if final_dmg > 0:
        dmg_color = console.Fore.YELLOW if is_crit else console.Fore.CYAN
        print(
            f"{console.colorize(attacker.name, console.Fore.GREEN)} ataca a "
            f"{console.colorize(defender.name, console.Fore.RED)} y hace "
            f"{console.colorize(str(final_dmg), dmg_color, bright=is_crit)} de daño"
            f"{console.crit_suffix(is_crit)}"
        )
    elif not is_immune_hit:
        # Inmunidad ya lo explica arriba ("el ataque no le hace nada"); un
        # segundo mensaje sería redundante. "Bloqueado" queda para cualquier
        # otra causa futura de daño 0 que no sea inmunidad elemental.
        print(f"{console.colorize(defender.name, console.Fore.BLUE)} ha bloqueado el ataque.")

    # Estado alterado del arma elemental, DESPUÉS de anunciar el golpe. Solo el
    # jugador; si el enemigo resiste el elemento, la probabilidad y la duración
    # se reducen a la mitad; si es inmune al elemento, no se aplica.
    if isinstance(attacker, Player) and hasattr(defender, "apply_status"):
        _try_inflict_weapon_status(attacker, defender, element)

    # Estado extra de la habilidad (aturdir / sangrado), si el objetivo sigue vivo.
    if defender.is_alive() and hasattr(defender, "apply_status"):
        if p.get("stun_chance") and random.random() < p["stun_chance"] and defender.apply_status("aturdido", 1):
            print(console.colorize(f"💫 ¡{defender.name} queda aturdido!", console.Fore.LIGHTYELLOW_EX, bright=True))
        if p.get("bleed_turns") and defender.apply_status("sangrado", p["bleed_turns"]):
            print(console.colorize(f"🩸 ¡{defender.name} empieza a sangrar!", console.Fore.RED))

        # Pasiva "Veneno de Contacto" (Pícaro): opción de envenenar en cada golpe.
        poison_chance = (
            attacker.passive_param("veneno_de_contacto", "on_hit_poison_chance", 0.0)
            if hasattr(attacker, "passive_param")
            else 0.0
        )
        if poison_chance and random.random() < poison_chance:
            if defender.apply_status("veneno", 3):
                print(console.colorize(f"🧪 ¡Tu contacto envenena a {defender.name}!", console.Fore.GREEN))
                reaction_msg = defender.pop_status_reaction_message()
                if reaction_msg:
                    print(reaction_msg)
            else:
                # La probabilidad acertó, pero el objetivo es inmune: decirlo,
                # si no parece que la pasiva nunca llegó siquiera a intentarlo.
                print(console.colorize(f"🧪 {defender.name} es inmune al veneno.", console.Fore.BLUE))

    if isinstance(attacker, Player):
        print_status(attacker, defender, defeated_enemies)
    else:
        print_status(defender, attacker, defeated_enemies)

    return final_dmg


def _try_inflict_weapon_status(player: "Player", enemy, element: str | None) -> None:
    """Si el arma equipada inflige un estado (explícito en `inflicts` o derivado
    de su elemento), lo tira. La resistencia del enemigo al elemento reduce a la
    mitad la probabilidad y la duración; la inmunidad al elemento lo anula."""
    # Desarmado: el arma no está en tus manos, así que no inflige nada
    # (igual que no cuenta su bonus de daño ni su elemento).
    if any(e["name"] == "desarmado" for e in player.status_effects):
        return
    # Reacción "fusión" ya consumida: el rayo acaba de romper el hielo en vez
    # de intentar paralizar, no lo intentemos también aquí.
    if getattr(enemy, "just_shattered", False):
        return
    weapon = player.equipped_weapon
    inflicts = weapon.get_inflicts() if weapon and hasattr(weapon, "get_inflicts") else None
    if not inflicts:
        return
    if element and enemy.affinity_for({element}) == 0.0:
        return  # inmune al elemento -> tampoco el estado

    chance = inflicts["chance"]
    duration = inflicts["duration"]
    if element and enemy.resists_element(element):
        chance *= 0.5
        duration = max(1, duration // 2)

    if random.random() < chance and enemy.apply_status(inflicts["status"], duration, inflicts.get("power", 0)):
        console.warning(_status_inflicted_message(enemy.name, inflicts["status"]))
        reaction_msg = enemy.pop_status_reaction_message()
        if reaction_msg:
            print(reaction_msg)


def _status_inflicted_message(name: str, status: str) -> str:
    """'X ha sido envenenado/quemado/...' (o un mensaje propio para estados sin
    participio natural como `fractura_magica`)."""
    override = f"combat.status_inflicted.{status}"
    if i18n.has(override):
        return i18n.t(override, name=name)
    verb = i18n.t(f"status.verb.{status}")
    if verb == f"status.verb.{status}":  # sin participio -> forma genérica
        verb = status_label(status)
    return i18n.t("combat.status_inflicted", name=name, verb=verb)


def _handle_victory(player, enemy, defeated_enemies: list, unlocked_enemies: list) -> tuple:
    print(f"\n{console.colorize(f'¡VICTORIA! {enemy.name} ha sido derrotado.', console.Fore.YELLOW, bright=True)}")

    player.enemy_kill_counts[enemy.name] = player.enemy_kill_counts.get(enemy.name, 0) + 1

    if enemy.name not in defeated_enemies:
        defeated_enemies.append(enemy.name)

        # Consultamos si este enemigo desbloquea a otro
        next_enemy = ENEMY_PROGRESSION.get(enemy.name)

        if next_enemy and next_enemy not in unlocked_enemies:
            unlocked_enemies.append(next_enemy)
            print(console.colorize(f"✨ ¡NUEVO ENEMIGO DESBLOQUEADO: {next_enemy}!", console.Fore.MAGENTA))

    # Recompensa de Oro
    gold = enemy.get_gold_drop()
    player.inventory.gold += gold
    print(f"💰 Oro obtenido: {console.colorize(str(gold), console.Fore.YELLOW)}")

    # Experiencia y Nivel
    old_level = player.level
    player.gain_experience(gold * 2)

    # Comprobamos si subió de nivel
    player.just_leveled_up = player.level > old_level

    # Recompensa de Ítems (Drops)
    drops = enemy.drop_item()
    if drops:
        print(console.colorize("\n--- BOTÍN ENCONTRADO ---", console.Fore.CYAN))
        from valeterna.items.equipment import Armor, Weapon
        from valeterna.items.factory import item_kind_label

        for item in drops:
            player.inventory.add_item(item)
            # Nombre + tipo + (solo armas/armaduras) las estadísticas que otorga.
            # Las pociones no: su descripción ya dice lo que hacen.
            kind = console.colorize(f"({item_kind_label(item)})", console.Fore.LIGHTBLACK_EX)
            extra = ""
            if isinstance(item, (Weapon, Armor)) and item.get_stats_info():
                extra = f" {console.colorize(f'[{item.get_stats_info()}]', console.Fore.LIGHTBLACK_EX)}"
            print(f"📦 {console.colorize(item.name, console.Fore.GREEN)} {kind}: {item.description}{extra}")

    # Pasiva "Segundo Aliento" (Vagabundo): curación al derrotar a un enemigo.
    for skill in player._active_passives():
        pct = skill.params.get("heal_on_kill_pct")
        if pct:
            healed = min(player.stats.max_health - player.stats.health, round(player.stats.max_health * pct))
            if healed > 0:
                player.stats.health += healed
                print(
                    console.colorize(
                        f"💚 {skill.name}: recuperas {healed} HP "
                        f"(vida: {player.stats.health}/{player.stats.max_health}).",
                        console.Fore.GREEN,
                    )
                )

    # Si sube de nivel, devolvemos el nuevo snapshot de stats
    return (player.stats.min_atk, player.stats.max_atk), player.stats.armor


def _handle_defeat(player, enemy=None, pause: bool = True) -> None:
    """Gestiona lo que ocurre cuando el jugador cae en combate. `pause=False`
    cuando estamos en una cadena: la pausa (y el resumen de botín) se hacen una
    sola vez al final. `enemy` (opcional, por compatibilidad con llamadas
    antiguas) marca en `mundo["banderas"]` que el jugador ha perdido alguna
    vez contra él — solo élite/guardián lo usan, para desbloquear su
    provocación desde el 2º encuentro (ver `_announce_encounter`)."""
    print("\n" + "x" * 60)
    print(console.colorize("¡HAS SIDO DERROTADO!", console.Fore.RED, bright=True))

    if enemy is not None and enemy.ENCOUNTER_KIND != "normal":
        player.mundo["banderas"].add(_defeat_flag(enemy))

    # Penalización de oro (ejemplo: pierdes el 30% de tu oro actual)
    penalty = player.inventory.gold // 3
    player.inventory.gold -= penalty

    # Restauración por "emergencia"
    player.stats.health = player.stats.max_health

    console.warning("Unos viajeros te han rescatado y llevado a la ciudad.")
    print(f"Penalización: Has perdido {console.colorize(f'{penalty} de oro', console.Fore.RED)}.")
    console.success("Tu salud ha sido restaurada para que puedas continuar.")
    print("x" * 60)
    if pause:
        console.ask("\nPresiona Enter para volver...")


def _restore_player(player, snapshot: dict, max_recovery: int | None = None) -> None:
    """Elimina efectos, restaura stats base y cura al jugador.

    `max_recovery`, si se indica (huida), limita la curación a como mucho la
    vida perdida durante ESTE combate — huir no es una victoria, así que no
    debería curar daño acumulado de peleas anteriores.
    """
    # Restaurar stats base (por si hubo pociones de fuerza/defensa)
    player.stats.min_atk, player.stats.max_atk = snapshot["atk"]
    player.stats.armor = snapshot["armor"]

    # Limpiar estados alterados
    player.status_effects = []
    player.defending = False
    player.battle_element = None  # el elemento elegido por "Sintonía" solo dura el combate
    player.mana_shield = False
    player.took_physical_hit = False

    if hasattr(player, "active_effects"):
        player.active_effects = []

    # Recuperar Salud al finalizar
    if player.is_alive():
        if player.just_leveled_up:
            print(console.colorize("✨ ¡Energía renovada por el nuevo nivel!", console.Fore.MAGENTA))
            player.just_leveled_up = False  # Reseteamos el flag
        else:
            # Lógica de curación normal (50% de lo perdido)
            missing_health = player.stats.max_health - player.stats.health
            if max_recovery is not None:
                missing_health = max(0, min(missing_health, max_recovery))
            recovery = missing_health // 2
            player.stats.health += recovery
            if recovery > 0:
                print(
                    f"\n{console.colorize(f'Tras el combate, descansas y recuperas {recovery} HP.', console.Fore.GREEN)}"
                )
                print(
                    console.colorize(
                        f"Vida actual: {player.stats.health}/{player.stats.max_health}", console.Fore.GREEN
                    )
                )
