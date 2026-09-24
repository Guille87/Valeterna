import getpass
import hashlib
import random
import sys
from functools import partial

from valeterna import __version__, updater
from valeterna.audio.resource_manager import ResourceManager
from valeterna.characters.classes import PROFILES, CharClass, starting_stats
from valeterna.characters.enemies import (
    AhogadoErrante,
    AngelCaido,
    AparicionDeLaCuadrilla,
    AranaTejesombras,
    Bandido,
    BibliotecarioErrante,
    CabraMontesCorrupta,
    CangrejoAcorazado,
    CarroneroDeCripta,
    ChamanDelCieno,
    ChamanGoblin,
    ChispaDelPuntal,
    CiudadanoHueco,
    CustodioArcano,
    CustodioDeVidrieras,
    Demonio,
    Dragon,
    DruidaCorrupto,
    EcoDeLaGuardia,
    ElAnegado,
    ElArchivista,
    ElCarnicero,
    ElDecimoquinto,
    ElEnraizado,
    ElSinRostro,
    EnjambrePolillas,
    EntCorrompido,
    EspantajoAnegado,
    EspectroDeLaGuardia,
    EspirituVengativo,
    Gargola,
    Goblin,
    GoblinMontaraz,
    GolemDePiedra,
    GuardiaCaida,
    GuardianDelTemploHundido,
    GuardianDelTomoProhibido,
    GuardianOsario,
    HeraldoDelAmo,
    HeraldoDeLaTormenta,
    HorrorDeProfundidad,
    Huargo,
    LoboUmbrio,
    MineroPoseido,
    MurcielagoDeTormenta,
    Nigromante,
    OgroDelYermo,
    Orc,
    OsoEspectral,
    RataGigante,
    SacerdoteAhogado,
    Salteador,
    SanguijuelaColosal,
    SerafinCorrupto,
    SerpienteDeFango,
    Skeleton,
    TomoViviente,
    Troll,
    VerdugoDeLaMina,
    VerdugoInfernal,
)
from valeterna.characters.enemies.mage import Mago
from valeterna.characters.player import Player
from valeterna.characters.skills import MAX_EQUIPPED_ACTIVES, SkillKind
from valeterna.characters.stats import Stats
from valeterna.combat.battle import initiate_battle
from valeterna.config import crash_reporting, secret_store, settings
from valeterna.items.equipment import ARMOR_SLOTS, Armor, Weapon, slot_label
from valeterna.items.materials import Material
from valeterna.persistence.save_load import load_game, save_exists
from valeterna.shop.shop import Shop
from valeterna.ui import console
from valeterna.ui.formatting import print_bestiary_entry

# Instancia global de ResourceManager
resource_manager = ResourceManager()

ALL_ENEMY_NAMES = [
    "Goblin",
    "Rata Gigante",
    "Goblin Montaraz",
    "Huargo",
    "Chamán Goblin",
    "Esqueleto",
    "Bandido",
    "Salteador",
    "Ogro del Yermo",
    "El Carnicero",
    "Orco",
    "Espíritu Vengativo",
    "Troll",
    "Araña Tejesombras",
    "Druida Corrupto",
    "Oso Espectral",
    "Enjambre de Polillas Pálidas",
    "Lobo Umbrío",
    "Ent Corrompido",
    "El Enraizado",
    "Sanguijuela Colosal",
    "Espantajo Anegado",
    "Ahogado Errante",
    "Chamán del Cieno",
    "Cangrejo Acorazado",
    "Serpiente de Fango",
    "Sacerdote Ahogado",
    "Horror de Profundidad",
    "Guardián del Templo Hundido",
    "El Anegado",
    "Gárgola",
    "Gólem de Piedra",
    "Minero Poseído",
    "Murciélago de Tormenta",
    "Chispa del Puntal",
    "Aparición de la Cuadrilla",
    "Verdugo de la Mina",
    "Cabra Montés Corrupta",
    "Heraldo de la Tormenta",
    "El Decimoquinto",
    "Mago",
    "Nigromante",
    "Tomo Viviente",
    "Guardián Osario",
    "Custodio Arcano",
    "Espectro de la Guardia",
    "Bibliotecario Errante",
    "Carroñero de Cripta",
    "Guardián del Tomo Prohibido",
    "El Archivista",
    "Ángel Caído",
    "Demonio",
    "Ciudadano Hueco",
    "Guardia Caída",
    "Serafín Corrupto",
    "Eco de la Guardia",
    "Custodio de Vidrieras",
    "Verdugo Infernal",
    "Heraldo del Amo",
    "El Sin Rostro",
    "Dragón",
]

# Hash SHA-256 de la contraseña de administrador. Vive en config/secrets.py
# (no versionado); si no está configurado, el modo admin queda desactivado y el
# nombre "admin" deja de ser especial. Nunca se maneja la contraseña en texto
# plano salvo en el instante de teclearla.
_ADMIN_PASSWORD_HASH = secret_store.get("ADMIN_PASSWORD_HASH")


def _check_admin_password() -> bool:
    """Pide la contraseña de admin (sin mostrarla en pantalla si la consola lo
    permite) y compara su hash contra el guardado, sin manejar nunca el texto
    plano más que en el momento de teclearla."""
    if not _ADMIN_PASSWORD_HASH:
        return False
    # `getpass` necesita un terminal real (lee la entrada en modo "crudo" para
    # ocultarla). En consolas que no lo son —p. ej. el panel "Run" de
    # PyCharm, distinto de su pestaña "Terminal"— no siempre lanza una
    # excepción: puede quedarse colgado aceptando Intro como si fuera texto
    # normal, sin terminar nunca la entrada. Comprobamos `isatty()` primero y,
    # si no hay terminal real, vamos directos a la entrada visible en vez de
    # arriesgarnos a ese cuelgue; el `try/except` sigue de red para otros
    # fallos de `getpass` en consolas que sí pasan la comprobación.
    if sys.stdin.isatty():
        try:
            entered = getpass.getpass("Contraseña de administrador: ")
        except Exception:
            entered = console.ask("Contraseña de administrador: ")
    else:
        entered = console.ask("Contraseña de administrador: ")
    return hashlib.sha256(entered.encode("utf-8")).hexdigest() == _ADMIN_PASSWORD_HASH


def _maybe_show_update_notice(*, in_game: bool) -> None:
    """Si el hilo de arranque encontró una versión nueva, lo recuerda. Se llama
    en cada redibujado del menú principal y al entrar en "Nueva Partida" /
    "Cargar Partida", para que no se pase por alto yendo rápido; también una vez
    al abrir la partida (con la nota de guardar y volver al menú)."""
    info = updater.available()
    if not info:
        return
    print(console.colorize(f"\n⬆  Versión nueva disponible: {info.tag}", console.Fore.GREEN, bright=True))
    if in_game:
        print(console.colorize("   Guarda la partida y vuelve al Menú Principal para actualizar.", console.Fore.GREEN))


def _update_flow(info: updater.UpdateInfo) -> None:
    """Descarga, verifica y aplica una actualización (reinicia el juego)."""
    print(console.colorize(f"\n--- ACTUALIZAR A {info.tag} ---", console.Fore.YELLOW))
    if info.notes:
        print(info.notes[:600])
    if console.ask("\n¿Descargar y aplicar ahora? El juego se reiniciará. (s/n): ").strip().lower() != "s":
        return

    def _progress(fraction: float) -> None:
        print(f"\rDescargando... {fraction * 100:3.0f}%", end="", flush=True)

    new_dir = updater.download_and_stage(info, on_progress=_progress)
    print()
    if not new_dir:
        console.error("No se pudo descargar o verificar la actualización. Inténtalo más tarde.")
        return
    console.success("Descarga verificada. Se abrirá una ventana para aplicar la actualización.")
    print(
        console.colorize(
            "El juego se cerrará ahora. Si no vuelve a abrirse solo en unos segundos, ábrelo tú: "
            "la actualización ya estará aplicada.",
            console.Fore.YELLOW,
        )
    )
    updater.apply_and_restart(new_dir)


def main_menu() -> None:
    resource_manager.set_mood("adventure")

    while True:
        # 1. Comprobamos si la música terminó y hay que poner otra
        resource_manager.update()
        _maybe_show_update_notice(in_game=False)

        print("\n" + "=" * 30)
        print(console.colorize("⚔️  MENÚ PRINCIPAL  ⚔️", console.Fore.YELLOW))
        print(console.colorize(f"v{__version__}", console.Fore.BLACK, bright=True))
        print("=" * 30)

        options: list[tuple[str, object]] = [
            ("Nueva Partida", start_new_game),
            ("Cargar Partida", load_saved_game),
            ("Opciones", open_options),
        ]
        pending = updater.available()
        if pending:
            options.append((f"Actualizar a {pending.tag}", partial(_update_flow, pending)))
        options.append(("Salir", "break"))

        for i, (text, _) in enumerate(options, 1):
            print(f"{i}. {text}")

        choice = console.ask(f"\nSelecciona (1-{len(options)}): ")
        if not choice.isdigit() or not (1 <= int(choice) <= len(options)):
            console.error("Opción inválida.")
            continue

        action = options[int(choice) - 1][1]
        if action == "break":
            break
        action()  # type: ignore[operator]


def _choose_class() -> CharClass:
    """Menú de elección de clase al crear personaje. Enter sin nada = Vagabundo."""
    options = list(PROFILES.values())
    print(console.colorize("\n--- ELIGE TU CLASE ---", console.Fore.CYAN))
    for idx, profile in enumerate(options, 1):
        print(
            f"{console.colorize(f'{idx}.', console.Fore.CYAN)} {console.colorize(profile.name, console.Fore.MAGENTA)}"
        )
        print(f"   {profile.identity}")

    while True:
        choice = console.ask(
            f"\nSelecciona una clase (1-{len(options)}, Enter = {PROFILES[CharClass.VAGABUNDO].name}): "
        ).strip()
        if not choice:
            return CharClass.VAGABUNDO
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return options[int(choice) - 1].id
        console.error("Opción no válida.")


def start_new_game() -> None:
    _maybe_show_update_notice(in_game=False)
    print(console.colorize("\n--- NUEVA AVENTURA ---", console.Fore.CYAN))
    name = ""  # Inicializa el nombre del jugador como una cadena vacía
    is_admin = False

    # Bucle while para seguir pidiendo al usuario que ingrese un nombre hasta que ingresen al menos un caracter.
    # "admin" es un nombre reservado: si se escribe pero la contraseña falla,
    # no se puede jugar con ese nombre en absoluto, hay que volver a elegir uno.
    while not name:
        candidate = console.ask("Introduce tu nombre: ").strip()
        if not candidate:
            continue

        if candidate.lower() == "admin":
            if _check_admin_password():
                is_admin = True
                name = candidate
            else:
                console.error('Contraseña incorrecta. El nombre "admin" está reservado, elige otro nombre.')
        elif save_exists(candidate):
            console.error(
                f'Ya existe una partida con el nombre "{candidate}". '
                f"Elige otro nombre o carga esa partida desde el menú principal."
            )
        else:
            name = candidate

    # --- LÓGICA DE CHEATS / ADMIN ---
    if is_admin:
        print(console.colorize("⚠️  MODO DESARROLLADOR ACTIVADO ⚠️", console.Fore.MAGENTA))
        # El admin también elige clase, para poder probarlas con stats de cheat.
        char_class = _choose_class()
        # Stats muy altas: Vida 500, Ataque 50-70, Armadura 20
        initial_stats = Stats(500, 500, 20, 40, 10, crit_chance=0.15)
        if char_class == CharClass.ARCANISTA:
            # Poder mágico a la par del ataque físico de cheat (20-40): 25 da un
            # rango mágico ~25-33, comparable, no el doble.
            initial_stats.magic_power = 25
        player = Player(name, initial_stats, char_class=char_class)
        console.success(f"Empiezas como {PROFILES[char_class].name}.")
        player.level = 10
        player.inventory.gold = 5000

        # Desbloqueamos todo para testear cualquier enemigo
        unlocked = list(ALL_ENEMY_NAMES)
        defeated = list(ALL_ENEMY_NAMES)
        player.enemy_kill_counts = {name: 1 for name in defeated}

    else:
        char_class = _choose_class()
        player = Player(name, starting_stats(char_class), char_class=char_class)
        console.success(f"Empiezas como {PROFILES[char_class].name}.")
        unlocked = ["Goblin"]
        defeated = []

    player.autoequip_skills()  # equipa las activas que ya conoce (1 al empezar)

    from valeterna.ui.exploration import zone_loop

    zone_loop(player, unlocked, defeated, is_admin=is_admin)


def load_saved_game() -> None:
    _maybe_show_update_notice(in_game=False)
    name = ""
    is_admin = False

    # Mismo nombre reservado que en Nueva Partida: cargar una partida guardada
    # como "admin" tampoco se permite sin acertar la contraseña.
    while not name:
        candidate = console.ask("Nombre del personaje a cargar: ").strip()
        if not candidate:
            continue

        if candidate.lower() == "admin":
            if _check_admin_password():
                is_admin = True
                name = candidate
            else:
                console.error('Contraseña incorrecta. El nombre "admin" está reservado, elige otro nombre.')
        else:
            name = candidate

    # Creamos un player temporal para que load_game lo rellene
    temp_player = Player(name, Stats(1, 1, 1, 1, 1))
    data = load_game(temp_player)

    if data:
        player_name, unlocked, defeated = data

        from valeterna.ui.exploration import zone_loop

        zone_loop(temp_player, unlocked, defeated, is_admin=is_admin)


def ask_crash_reporting_opt_in() -> None:
    """Pregunta una sola vez (al arrancar) si el jugador quiere enviar informes
    de error automáticamente. Solo se llama si hay un webhook configurado y el
    jugador todavía no ha decidido."""
    if settings.load_crash_reporting() != settings.CRASH_REPORTS_UNSET:
        return

    print(console.colorize("\n--- INFORMES DE ERROR ---", console.Fore.YELLOW))
    print("¿Enviar automáticamente un informe si el juego se cierra por un fallo?")
    print("Ayuda a arreglar bugs más rápido.\n")
    print(
        console.colorize("Se envía:", console.Fore.CYAN)
        + " versión del juego, sistema operativo y el detalle técnico del error."
    )
    print(
        console.colorize("NO se envía:", console.Fore.CYAN)
        + " tu partida, tu nombre de usuario de Windows ni datos personales.\n"
    )
    print("Puedes cambiarlo cuando quieras en Opciones.")
    print("1. Sí, enviar informes")
    print("2. No, gracias")

    choice = console.ask("\nElige (1-2): ").strip()
    enabled = choice == "1"
    settings.save_crash_reporting(enabled)
    console.success("Informes de error activados. ¡Gracias!" if enabled else "De acuerdo, no se enviará nada.")


def _crash_reporting_label() -> str:
    state = settings.load_crash_reporting()
    if state is True:
        return "Activados"
    if state is False:
        return "Desactivados"
    return "Sin configurar"


def _check_updates_now() -> None:
    """Comprobación manual de actualizaciones desde Opciones."""
    print("Comprobando...")
    info = updater.check()
    if info:
        console.success(f"¡Hay una versión nueva! {info.tag}. Actualiza desde el Menú Principal.")
    else:
        console.info(f"Estás en la última versión ({updater._current_version()}), o no se pudo comprobar.")


def open_options() -> None:
    music_vol, sfx_vol = settings.load_config()

    while True:
        options: list[tuple[str, str]] = [
            (f"Música (actual: {int(music_vol * 10)})", "music"),
            (f"Efectos (actual: {int(sfx_vol * 10)})", "sfx"),
        ]
        if updater.is_active():
            estado = "activado" if settings.load_update_check() else "desactivado"
            options.append((f"Aviso de actualizaciones ({estado})", "upd_toggle"))
            options.append(("Buscar actualizaciones ahora", "upd_check"))
        if crash_reporting.is_configured():
            options.append((f"Informes de error ({_crash_reporting_label()})", "reports"))
        options.append(("Volver", "back"))

        print(console.colorize("\n--- AJUSTES ---", console.Fore.YELLOW))
        for i, (label, _) in enumerate(options, 1):
            print(f"{i}. {label}")

        choice = console.ask("\nSelecciona una opción: ")
        if not choice.isdigit() or not (1 <= int(choice) <= len(options)):
            console.error("Opción no válida.")
            continue
        key = options[int(choice) - 1][1]

        if key == "back":
            break
        elif key == "music":
            vol = console.ask("Volumen Música (0-10): ")
            if vol.isdigit() and 0 <= int(vol) <= 10:
                music_vol = int(vol) / 10
                resource_manager.set_volume_music(music_vol)
                settings.save_config(music_vol, sfx_vol)
                console.success("Música ajustada.")
        elif key == "sfx":
            vol = console.ask("Volumen Efectos (0-10): ")
            if vol.isdigit() and 0 <= int(vol) <= 10:
                sfx_vol = int(vol) / 10
                resource_manager.set_volume_sfx(sfx_vol)
                settings.save_config(music_vol, sfx_vol)
                resource_manager.play_sfx("level_up")  # Feedback auditivo
                console.success("Efectos ajustados.")
        elif key == "reports":
            current = settings.load_crash_reporting() is True
            settings.save_crash_reporting(not current)
            console.success("Informes de error activados." if not current else "Informes de error desactivados.")
        elif key == "upd_toggle":
            new_value = not settings.load_update_check()
            settings.save_update_check(new_value)
            console.success(
                "Aviso de actualizaciones activado." if new_value else "Aviso de actualizaciones desactivado."
            )
        elif key == "upd_check":
            _check_updates_now()


def _skills_flow(player) -> None:
    """Menú de habilidades: muestra las pasivas (siempre activas) y deja
    equipar / quitar hasta 4 activas para llevar al combate."""
    known = player.known_skills()
    passives = [s for s in known if s.kind is SkillKind.PASSIVE]
    actives = [s for s in known if s.is_active]

    while True:
        print(console.colorize(f"\n--- HABILIDADES ({player.class_name}) ---", console.Fore.MAGENTA))
        if not known:
            print("Todavía no has aprendido ninguna habilidad. Sube de nivel.")
            return

        if passives:
            print(console.colorize("Pasivas (siempre activas):", console.Fore.CYAN))
            for s in passives:
                print(f"  · {console.colorize(s.name, console.Fore.MAGENTA)} — {console.tint_status(s.description)}")

        print(
            console.colorize(
                f"\nActivas equipadas: {len(player.equipped_skills)}/{MAX_EQUIPPED_ACTIVES}", console.Fore.CYAN
            )
        )
        for idx, s in enumerate(actives, 1):
            mark = console.colorize("[✔]", console.Fore.GREEN) if s.id in player.equipped_skills else "[ ]"
            cd = f" · enfriamiento {s.cooldown}" if s.cooldown else ""
            print(
                f"{console.colorize(f'{idx}.', console.Fore.CYAN)} {mark} {console.colorize(s.name, console.Fore.MAGENTA)}{cd}"
            )
            print(f"     {console.tint_status(s.description)}")
        print(f"{console.colorize(f'{len(actives) + 1}.', console.Fore.CYAN)} Volver")

        choice = console.ask("\nElige una activa para equipar/quitar: ").strip()
        if not choice.isdigit():
            console.error("Opción no válida.")
            continue
        idx = int(choice) - 1
        if idx == len(actives):
            return
        if not (0 <= idx < len(actives)):
            console.error("Opción fuera de rango.")
            continue

        skill = actives[idx]
        if skill.id in player.equipped_skills:
            player.equipped_skills.remove(skill.id)
            console.info(f"{skill.name} desequipada.")
        elif len(player.equipped_skills) >= MAX_EQUIPPED_ACTIVES:
            console.error(f"Ya llevas {MAX_EQUIPPED_ACTIVES} activas equipadas. Quita una primero.")
        else:
            player.equipped_skills.append(skill.id)
            console.success(f"{skill.name} equipada.")


def _equip_armor_flow(player) -> None:
    """Submenú para elegir en qué hueco de armadura equipar algo."""
    while True:
        print(console.colorize("\n--- EQUIPAR ARMADURA ---", console.Fore.YELLOW))
        for idx, slot in enumerate(ARMOR_SLOTS, 1):
            equipped = player.equipped_armor.get(slot)
            if equipped:
                label = f"{console.colorize(equipped.name, console.Fore.BLUE)} ({equipped.get_stats_info()})"
            else:
                label = "-- vacío --"
            print(f"{idx}. {slot_label(slot)}: {label}")
        print(f"{len(ARMOR_SLOTS) + 1}. Volver")

        choice = console.ask(f"\nElige un hueco (1-{len(ARMOR_SLOTS) + 1}): ")
        if not choice.isdigit():
            console.error("Entrada no válida.")
            continue

        idx = int(choice) - 1
        if idx == len(ARMOR_SLOTS):
            return
        if not (0 <= idx < len(ARMOR_SLOTS)):
            console.error("Opción fuera de rango.")
            continue

        player.inventory.equip_menu(Armor, filter_slot=ARMOR_SLOTS[idx])


def _bestiary_flow(player, defeated_enemies: list) -> None:
    """Submenú de solo lectura con la ficha de los enemigos ya derrotados alguna vez."""
    while True:
        print(console.colorize("\n--- BESTIARIO ---", console.Fore.YELLOW))

        if not defeated_enemies:
            print("Todavía no has derrotado a ningún enemigo.")
            console.ask("\nPresiona Enter para volver...")
            return

        for idx, name in enumerate(defeated_enemies, 1):
            print(f"{idx}. {name}")
        print(f"{len(defeated_enemies) + 1}. Volver")

        choice = console.ask(f"\nElige un enemigo (1-{len(defeated_enemies) + 1}): ")
        if not choice.isdigit():
            console.error("Entrada no válida.")
            continue

        idx = int(choice) - 1
        if idx == len(defeated_enemies):
            return
        if not (0 <= idx < len(defeated_enemies)):
            console.error("Opción fuera de rango.")
            continue

        enemy_name = defeated_enemies[idx]
        print_bestiary_entry(_get_enemy_instance(enemy_name), player.enemy_kill_counts.get(enemy_name, 0))
        console.ask("\nPresiona Enter para continuar...")


# Estadísticas editables desde el Panel de Admin: (atributo en Stats, etiqueta, tipo).
_ADMIN_STAT_FIELDS = [
    ("health", "Vida actual", int),
    ("max_health", "Vida máxima", int),
    ("min_atk", "Ataque mínimo", int),
    ("max_atk", "Ataque máximo", int),
    ("armor", "Armadura", int),
    ("magic_resist", "Resistencia Mágica", int),
    ("speed", "Velocidad", int),
    ("precision", "Precisión", int),
    ("evasion", "Evasión", int),
    ("armor_penetration", "Penetración de Armadura", int),
    ("magic_penetration", "Penetración Mágica", int),
    ("regen", "Regeneración", int),
    ("crit_chance", "Prob. Crítico (0.0-1.0)", float),
    ("crit_damage", "Daño Crítico (multiplicador, ej. 1.5)", float),
]


def _admin_panel_flow(player, unlocked_enemies: list, defeated_enemies: list) -> None:
    """Control total del personaje de pruebas 'admin': oro, nivel, cualquier
    estadística y combate directo contra cualquier enemigo sin restricciones."""
    while True:
        print(console.colorize("\n--- PANEL DE ADMIN ---", console.Fore.MAGENTA, bright=True))
        options = [
            ("Poner oro", lambda: _admin_set_gold(player)),
            ("Poner nivel", lambda: _admin_set_level(player)),
            ("Editar estadísticas", lambda: _admin_edit_stats(player)),
            ("Curación completa", lambda: _admin_full_heal(player)),
            (
                "Desbloquear y marcar como derrotados todos los enemigos",
                lambda: _admin_unlock_all(player, unlocked_enemies, defeated_enemies),
            ),
            (
                "Combate directo contra cualquier enemigo",
                lambda: _admin_direct_battle(player, defeated_enemies, unlocked_enemies),
            ),
            (
                "Conseguir todos los materiales (desbloquea también sus recetas)",
                lambda: _admin_give_all_materials(player),
            ),
            ("Conseguir todas las armas y armaduras de los enemigos", lambda: _admin_give_all_equipment(player)),
            ("Conseguir todas las pociones (x20 de cada)", lambda: _admin_give_all_potions(player)),
            ("Volver", "break"),
        ]

        for i, (text, _) in enumerate(options, 1):
            print(f"{i}. {text}")

        choice = console.ask(f"\nElige (1-{len(options)}): ")
        if not choice.isdigit():
            console.error("Entrada no válida.")
            continue

        idx = int(choice) - 1
        if idx == len(options) - 1:
            return
        if not (0 <= idx < len(options)):
            console.error("Opción fuera de rango.")
            continue

        options[idx][1]()


def _admin_set_gold(player) -> None:
    value = console.ask(f"Nuevo oro (actual {player.inventory.gold}): ")
    if not value.isdigit():
        console.error("Entrada no válida.")
        return
    player.inventory.gold = int(value)
    console.success(f"Oro puesto a {player.inventory.gold}.")


def _admin_set_level(player) -> None:
    value = console.ask(f"Nuevo nivel (actual {player.level}): ")
    if not value.isdigit() or int(value) < 1:
        console.error("Entrada no válida.")
        return

    target = int(value)
    if target > player.level:
        # Reutiliza la curva de subida de nivel real, así las stats suben de
        # forma coherente con lo que tocaría a ese nivel en una partida normal.
        while player.level < target:
            player._level_up()
        console.success(f"Nivel subido a {player.level} (estadísticas recalculadas con la curva normal de subida).")
    elif target < player.level:
        player.level = target
        console.warning(
            f"Nivel bajado a {player.level} — las estadísticas no bajan solas, edítalas a mano si hace falta."
        )
    else:
        console.info("Ya estás en ese nivel.")


def _admin_edit_stats(player) -> None:
    while True:
        print(console.colorize("\n--- EDITAR ESTADÍSTICAS ---", console.Fore.MAGENTA))
        for idx, (attr, label, _) in enumerate(_ADMIN_STAT_FIELDS, 1):
            print(f"{idx}. {label}: {getattr(player.stats, attr)}")
        print(f"{len(_ADMIN_STAT_FIELDS) + 1}. Volver")

        choice = console.ask(f"\nElige qué editar (1-{len(_ADMIN_STAT_FIELDS) + 1}): ")
        if not choice.isdigit():
            console.error("Entrada no válida.")
            continue

        idx = int(choice) - 1
        if idx == len(_ADMIN_STAT_FIELDS):
            return
        if not (0 <= idx < len(_ADMIN_STAT_FIELDS)):
            console.error("Opción fuera de rango.")
            continue

        attr, label, cast = _ADMIN_STAT_FIELDS[idx]
        raw = console.ask(f"Nuevo valor para {label}: ")
        try:
            value = cast(raw)
        except ValueError:
            console.error("Entrada no válida.")
            continue

        setattr(player.stats, attr, value)
        # Leemos el valor de vuelta en vez de echar el que escribió el usuario:
        # "health" tiene un setter que lo recorta a max_health, por ejemplo.
        console.success(f"{label} puesto a {getattr(player.stats, attr)}.")


def _admin_full_heal(player) -> None:
    player.stats.health = player.stats.max_health
    console.success("Vida restaurada al máximo.")


def _admin_unlock_all(player, unlocked_enemies: list, defeated_enemies: list) -> None:
    for name in ALL_ENEMY_NAMES:
        if name not in unlocked_enemies:
            unlocked_enemies.append(name)
        if name not in defeated_enemies:
            defeated_enemies.append(name)
        player.enemy_kill_counts.setdefault(name, 1)
    console.success("Todos los enemigos desbloqueados y marcados como derrotados (Bestiario incluido).")


def _admin_direct_battle(player, defeated_enemies: list, unlocked_enemies: list) -> None:
    """Combate contra cualquier enemigo, sin importar si está desbloqueado todavía."""
    print(console.colorize("\n--- COMBATE DIRECTO (ADMIN) ---", console.Fore.MAGENTA))
    for idx, name in enumerate(ALL_ENEMY_NAMES, 1):
        print(f"{idx}. {name}")
    print(f"{len(ALL_ENEMY_NAMES) + 1}. Volver")

    choice = console.ask(f"\nElige un enemigo (1-{len(ALL_ENEMY_NAMES) + 1}): ")
    if not choice.isdigit():
        console.error("Entrada no válida.")
        return

    idx = int(choice) - 1
    if idx == len(ALL_ENEMY_NAMES):
        return
    if not (0 <= idx < len(ALL_ENEMY_NAMES)):
        console.error("Opción fuera de rango.")
        return

    enemy_name = ALL_ENEMY_NAMES[idx]
    initiate_battle(
        player,
        _get_enemy_instance(enemy_name),
        defeated_enemies,
        unlocked_enemies,
        enemy_factory=lambda: _get_enemy_instance(enemy_name),
    )


def _collect_all_possible_drops() -> list:
    """Fuerza random.random() a 0 mientras se piden los drops de los 14
    enemigos, para que caigan absolutamente todos los objetos posibles de
    cada uno (en vez de solo los que la tirada real habría dado)."""
    original_random = random.random
    random.random = lambda: 0.0
    try:
        drops = []
        for name in ALL_ENEMY_NAMES:
            drops.extend(_get_enemy_instance(name).drop_item())
        return drops
    finally:
        random.random = original_random


def _admin_give_all_materials(player) -> None:
    """Da 50 unidades de cada material del juego (y, de paso, descubre las
    recetas de la herrería que los piden, ya que Inventory.add_item() marca
    un Material como descubierto la primera vez que se consigue)."""
    seen = set()
    for item in _collect_all_possible_drops():
        if isinstance(item, Material) and item.name not in seen:
            seen.add(item.name)
            player.inventory.add_item(item, 50, announce=False)
    console.success(
        f"Conseguidas 50 unidades de cada uno de los {len(seen)} materiales del juego. "
        f"Todas las recetas de la herrería ya deberían estar descubiertas."
    )


def _admin_give_all_equipment(player) -> None:
    """Da una copia de cada arma y armadura que puede soltar algún enemigo."""
    equipment = [item for item in _collect_all_possible_drops() if isinstance(item, (Weapon, Armor))]
    for item in equipment:
        player.inventory.add_item(item, announce=False)
    console.success(
        f"Conseguidas {len(equipment)} armas y armaduras: una de cada objeto que puede soltar algún enemigo."
    )


def _admin_give_all_potions(player) -> None:
    """Da 20 unidades de cada poción de la tienda (salud, regeneración, fuerza, antídoto)."""
    from valeterna.items.factory import item_factory

    potions = [entry.template for entry in Shop().catalog if entry.stackable]
    for template in potions:
        player.inventory.add_item(item_factory(template.to_dict()), 20, announce=False)
    console.success(f"Conseguidas 20 unidades de cada una de las {len(potions)} pociones.")


def _get_enemy_instance(name: str):
    """Convierte un string en una instancia de clase de enemigo."""
    enemies = {
        "Goblin": Goblin,
        "Rata Gigante": RataGigante,
        "Goblin Montaraz": GoblinMontaraz,
        "Huargo": Huargo,
        "Chamán Goblin": ChamanGoblin,
        "Esqueleto": Skeleton,
        "Bandido": Bandido,
        "Salteador": Salteador,
        "Ogro del Yermo": OgroDelYermo,
        "El Carnicero": ElCarnicero,
        "Orco": Orc,
        "Espíritu Vengativo": EspirituVengativo,
        "Troll": Troll,
        "Araña Tejesombras": AranaTejesombras,
        "Druida Corrupto": DruidaCorrupto,
        "Oso Espectral": OsoEspectral,
        "Enjambre de Polillas Pálidas": EnjambrePolillas,
        "Lobo Umbrío": LoboUmbrio,
        "Ent Corrompido": EntCorrompido,
        "El Enraizado": ElEnraizado,
        "Sanguijuela Colosal": SanguijuelaColosal,
        "Espantajo Anegado": EspantajoAnegado,
        "Ahogado Errante": AhogadoErrante,
        "Chamán del Cieno": ChamanDelCieno,
        "Cangrejo Acorazado": CangrejoAcorazado,
        "Serpiente de Fango": SerpienteDeFango,
        "Sacerdote Ahogado": SacerdoteAhogado,
        "Horror de Profundidad": HorrorDeProfundidad,
        "Guardián del Templo Hundido": GuardianDelTemploHundido,
        "El Anegado": ElAnegado,
        "Gárgola": Gargola,
        "Gólem de Piedra": GolemDePiedra,
        "Minero Poseído": MineroPoseido,
        "Murciélago de Tormenta": MurcielagoDeTormenta,
        "Chispa del Puntal": ChispaDelPuntal,
        "Aparición de la Cuadrilla": AparicionDeLaCuadrilla,
        "Verdugo de la Mina": VerdugoDeLaMina,
        "Cabra Montés Corrupta": CabraMontesCorrupta,
        "Heraldo de la Tormenta": HeraldoDeLaTormenta,
        "El Decimoquinto": ElDecimoquinto,
        "Mago": Mago,
        "Nigromante": Nigromante,
        "Tomo Viviente": TomoViviente,
        "Guardián Osario": GuardianOsario,
        "Custodio Arcano": CustodioArcano,
        "Espectro de la Guardia": EspectroDeLaGuardia,
        "Bibliotecario Errante": BibliotecarioErrante,
        "Carroñero de Cripta": CarroneroDeCripta,
        "Guardián del Tomo Prohibido": GuardianDelTomoProhibido,
        "El Archivista": ElArchivista,
        "Ángel Caído": AngelCaido,
        "Demonio": Demonio,
        "Ciudadano Hueco": CiudadanoHueco,
        "Guardia Caída": GuardiaCaida,
        "Serafín Corrupto": SerafinCorrupto,
        "Eco de la Guardia": EcoDeLaGuardia,
        "Custodio de Vidrieras": CustodioDeVidrieras,
        "Verdugo Infernal": VerdugoInfernal,
        "Heraldo del Amo": HeraldoDelAmo,
        "El Sin Rostro": ElSinRostro,
        "Dragón": Dragon,
    }
    # Si el nombre no existe, por defecto crea un Goblin para evitar errores
    return enemies.get(name, Goblin)()
