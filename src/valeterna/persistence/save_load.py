import base64
import binascii
import contextlib
import json
import os
import shutil

from valeterna.config.paths import SAVE_DIR
from valeterna.items.equipment import ARMOR_SLOTS
from valeterna.items.factory import item_factory
from valeterna.ui import console


def check_save_directory() -> None:
    """Asegura la existencia de la carpeta de guardado."""
    if not os.path.exists(SAVE_DIR):
        try:
            os.makedirs(SAVE_DIR)
        except OSError as e:
            console.error(f"No se pudo crear la carpeta de guardado: {e}")


def save_game(player, unlocked_enemies: list, defeated_enemies: list) -> None:
    """Serializa, crea backup y guarda el estado del juego."""
    check_save_directory()

    file_path = os.path.join(SAVE_DIR, f"{player.name}.sav")
    backup_path = os.path.join(SAVE_DIR, f"{player.name}.bak")

    # --- LÓGICA DE BACKUP ---
    # Si ya existe una partida guardada, la renombramos a .bak antes de escribir la nueva
    if os.path.exists(file_path):
        try:
            shutil.copy2(file_path, backup_path)  # copy2 preserva metadatos
        except Exception as e:
            console.warning(f"Aviso: No se pudo crear el backup: {e}")

    # Delegamos la creación del diccionario de stats al objeto stats (Encapsulamiento)
    save_data = {
        "player_name": player.name,
        "unlocked_enemies": unlocked_enemies,
        "defeated_enemies": defeated_enemies,
        "gold": player.inventory.gold,
        "clase": player.char_class.value,
        "habilidades_equipadas": list(player.equipped_skills),
        "player_stats": {
            "level": player.level,
            "experience": player.experience,
            "health": player.stats.health,
            "max_health": player.stats.max_health,
            "min_atk": player.stats.min_atk,
            "max_atk": player.stats.max_atk,
            "armor": player.stats.armor,
            "magic_resist": player.stats.magic_resist,
            "speed": player.stats.speed,
            "precision": player.stats.precision,
            "evasion": player.stats.evasion,
            "armor_penetration": player.stats.armor_penetration,
            "magic_penetration": player.stats.magic_penetration,
            "regen": player.stats.regen,
            "magic_power": player.stats.magic_power,
        },
        # Usamos list comprehension para el inventario
        "inventory": [item.to_dict() for item in player.inventory.items],
        "inventory_quantities": player.inventory.quantities,
        "discovered_materials": sorted(player.inventory.discovered_materials),
        "enemy_kill_counts": player.enemy_kill_counts,
        "equipped_weapon": player.equipped_weapon.to_dict() if player.equipped_weapon else None,
        "equipped_armor": {slot: item.to_dict() if item else None for slot, item in player.equipped_armor.items()},
    }

    try:
        json_str = json.dumps(save_data)
        encoded_data = base64.b64encode(json_str.encode("utf-8"))

        file_path = os.path.join(SAVE_DIR, f"{player.name}.sav")
        with open(file_path, "wb") as f:
            f.write(encoded_data)
        console.success(f"¡Progreso de {player.name} guardado con éxito!")
    except PermissionError:
        console.error(f"Error: No tienes permisos para escribir en {SAVE_DIR}.")
    except TypeError as e:
        console.error(f"Error de serialización: Algún objeto no se puede convertir a JSON. {e}")
    except Exception as e:
        console.error(f"Error inesperado al guardar: {e}")


def _resolve_save_name(name: str) -> str:
    """Devuelve el nombre real con el que está guardada la partida, buscando sin
    distinguir mayúsculas/minúsculas: así "guille" carga la partida de "Guille".
    Si no hay ninguna coincidencia, devuelve el nombre tal cual se escribió."""
    if os.path.exists(os.path.join(SAVE_DIR, f"{name}.sav")):
        return name
    if not os.path.isdir(SAVE_DIR):
        return name
    target = f"{name.lower()}.sav"
    for entry in os.listdir(SAVE_DIR):
        if entry.lower() == target:
            return entry[: -len(".sav")]
    return name


def save_exists(name: str) -> bool:
    """¿Ya hay una partida guardada con este nombre (sin distinguir
    mayúsculas/minúsculas)? Usado por "Nueva Partida" para no crear dos
    personajes casi homónimos que compartirían archivo de guardado."""
    resolved = _resolve_save_name(name)
    return os.path.exists(os.path.join(SAVE_DIR, f"{resolved}.sav")) or os.path.exists(
        os.path.join(SAVE_DIR, f"{resolved}.bak")
    )


def load_game(player):
    """Carga y reconstruye el estado del jugador desde un archivo. Intenta usar backup si el original falla."""
    resolved_name = _resolve_save_name(player.name)
    file_path = os.path.join(SAVE_DIR, f"{resolved_name}.sav")
    backup_path = os.path.join(SAVE_DIR, f"{resolved_name}.bak")

    # Si no existe el principal, pero sí el backup, intentamos restaurar el backup
    if not os.path.exists(file_path) and os.path.exists(backup_path):
        console.warning("Archivo principal no encontrado. Restaurando desde backup...")
        with contextlib.suppress(OSError):
            shutil.copy2(backup_path, file_path)

    if not os.path.exists(file_path):
        console.error(f"No se encontró ninguna partida guardada para {player.name}.")
        return None

    try:
        # Intentamos cargar el principal
        return _perform_load(player, file_path)
    except (json.JSONDecodeError, binascii.Error, UnicodeDecodeError):
        console.error("El archivo de guardado está corrupto o no es válido.")
        return None
    except KeyError as e:
        console.error(f"Falta un dato esperado en el archivo de guardado: {e}")
    except Exception as e:
        if os.path.exists(backup_path):
            console.warning(f"Fallo en el archivo principal. Intentando con el backup...{e}")
            return _perform_load(player, backup_path)
        return None


def _perform_load(player, path):
    """Función auxiliar para realizar la carga física desde un path determinado."""
    with open(path, "rb") as f:
        encoded_data = f.read()

    decoded_bytes = base64.b64decode(encoded_data)
    save_data = json.loads(decoded_bytes.decode("utf-8"))

    # Restauramos el nombre canónico (el que se usó al crear/guardar la partida),
    # no el que el jugador acaba de teclear en el prompt: así "guille" carga la
    # partida y a partir de ahí el personaje se llama "Guille" en todos lados
    # (pantallas, guardado posterior, nombre de archivo...).
    player.name = save_data["player_name"]

    stats_data = save_data["player_stats"]
    player.level = stats_data["level"]
    player.experience = stats_data["experience"]
    player.stats.max_health = stats_data["max_health"]
    player.stats.health = stats_data["health"]
    player.stats.min_atk = stats_data["min_atk"]
    player.stats.max_atk = stats_data["max_atk"]
    # Compatibilidad con partidas guardadas antes de renombrar "defense" a "armor"
    # y de añadir "magic_resist" (que no existía en absoluto).
    player.stats.armor = stats_data.get("armor", stats_data.get("defense", 0))
    player.stats.magic_resist = stats_data.get("magic_resist", 0)
    # Compatibilidad con partidas guardadas antes de añadir la velocidad (sistema ATB).
    player.stats.speed = stats_data.get("speed", 10)
    # Compatibilidad con partidas guardadas antes de añadir precisión/evasión.
    player.stats.precision = stats_data.get("precision", 0)
    player.stats.evasion = stats_data.get("evasion", 0)
    # Compatibilidad con partidas guardadas antes de añadir penetración de armadura/mágica.
    player.stats.armor_penetration = stats_data.get("armor_penetration", 0)
    player.stats.magic_penetration = stats_data.get("magic_penetration", 0)
    # Compatibilidad con partidas guardadas antes de añadir regeneración de salud.
    player.stats.regen = stats_data.get("regen", 0)
    # Compatibilidad con partidas guardadas antes de las clases de personaje
    # (v0.10.0): sin "clase" -> Vagabundo; sin poder mágico -> 0; sin
    # habilidades equipadas -> ninguna.
    player.stats.magic_power = stats_data.get("magic_power", 0)
    player.char_class = save_data.get("clase")
    player.equipped_skills = list(save_data.get("habilidades_equipadas", []))
    # Descarta ids inválidos (habilidad desconocida, no aprendida aún, o de otra
    # clase si la partida es anterior a las clases) y respeta el tope de 4.
    player.sanitize_equipped_skills()
    if not player.equipped_skills:
        player.autoequip_skills()

    player.inventory.gold = save_data.get("gold", 0)
    items_reconstructed = [item_factory(data) for data in save_data.get("inventory", [])]
    player.inventory.load_saved_inventory(items_reconstructed, save_data.get("inventory_quantities", {}))
    # Compatibilidad con partidas guardadas antes de añadir el descubrimiento de
    # materiales: si no hay "discovered_materials" en el guardado, al menos los
    # materiales que el jugador tiene ahora mismo en el inventario cuentan como
    # descubiertos (mejor eso que perder recetas ya desbloqueadas al cargar).
    materials_in_save = {data.get("name") for data in save_data.get("inventory", []) if data.get("type") == "Material"}
    player.inventory.discovered_materials = set(save_data.get("discovered_materials", [])) | materials_in_save

    # Compatibilidad con partidas guardadas antes de contar derrotas: si un
    # enemigo ya está en defeated_enemies, como mínimo se le ha ganado 1 vez.
    kill_counts = dict(save_data.get("enemy_kill_counts", {}))
    for name in save_data.get("defeated_enemies", []):
        kill_counts.setdefault(name, 1)
    player.enemy_kill_counts = kill_counts

    if save_data.get("equipped_weapon"):
        player.equipped_weapon = item_factory(save_data["equipped_weapon"])

    # Compatibilidad: antes de los huecos de armadura, "equipped_armor" era una
    # única pieza (o None) en vez de un dict {hueco: pieza-o-None}.
    player.equipped_armor = {slot: None for slot in ARMOR_SLOTS}
    equipped_armor_data = save_data.get("equipped_armor")
    if isinstance(equipped_armor_data, dict) and "type" in equipped_armor_data:
        # Formato antiguo: una sola pieza -> va al hueco "peto"
        old_item = item_factory(equipped_armor_data)
        if old_item:
            player.equipped_armor[getattr(old_item, "slot", "peto")] = old_item
    elif isinstance(equipped_armor_data, dict):
        # Formato nuevo: dict de hueco -> datos del ítem (o None)
        for slot, item_data in equipped_armor_data.items():
            if slot in player.equipped_armor and item_data:
                player.equipped_armor[slot] = item_factory(item_data)

    console.info(f"Carga exitosa desde: {os.path.basename(path)}")
    return save_data["player_name"], save_data["unlocked_enemies"], save_data["defeated_enemies"]
