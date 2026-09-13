import base64
import json

from valeterna.characters.player import Player
from valeterna.characters.stats import Stats
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.potions.healing_potion import HealingPotion
from valeterna.persistence import save_load
from valeterna.persistence.save_load import load_game, save_exists, save_game


def _build_player(name="Guille"):
    p = Player(name, Stats(health=80, max_health=100, min_atk=5, max_atk=10, armor=2, magic_resist=1))
    p.level = 3
    p.experience = 15
    p.inventory.gold = 42
    p.inventory.add_item(HealingPotion("Poción de Salud", "desc", 2, 20))
    p.equipped_weapon = Weapon("Espada", "desc", 5, damage=4)
    p.equipped_armor["casco"] = Armor("Casco", "desc", 8, slot="casco", defense=5)
    p.equipped_armor["guantes"] = Armor("Guantes de Combate", "desc", 15, slot="guantes", crit_chance=0.05)
    p.equipped_armor["anillo1"] = Armor("Anillo de Fuerza", "desc", 16, slot="anillo", damage=3)
    p.equipped_armor["anillo2"] = Armor("Anillo de Precisión", "desc", 20, slot="anillo", crit_damage=0.12)
    p.equipped_armor["amuleto"] = Armor("Amuleto de Resistencia", "desc", 28, slot="amuleto", magic_resist=5)
    p.enemy_kill_counts = {"Goblin": 3, "Esqueleto": 1}
    return p


def test_save_and_load_round_trip(tmp_save_dir):
    original = _build_player()
    save_game(original, unlocked_enemies=["Goblin", "Esqueleto"], defeated_enemies=["Goblin"])

    loaded_player = Player(original.name, Stats(1, 1, 1, 1, 1))
    result = load_game(loaded_player)

    assert result is not None
    player_name, unlocked, defeated = result
    assert player_name == "Guille"
    assert unlocked == ["Goblin", "Esqueleto"]
    assert defeated == ["Goblin"]

    assert loaded_player.level == 3
    assert loaded_player.experience == 15
    assert loaded_player.stats.health == 80
    assert loaded_player.stats.armor == 2
    assert loaded_player.stats.magic_resist == 1
    assert loaded_player.inventory.gold == 42
    assert loaded_player.inventory.quantities["Poción de Salud"] == 1
    assert loaded_player.equipped_weapon.name == "Espada"
    assert loaded_player.equipped_armor["casco"].name == "Casco"
    assert loaded_player.equipped_armor["guantes"].name == "Guantes de Combate"
    assert loaded_player.equipped_armor["anillo1"].name == "Anillo de Fuerza"
    assert loaded_player.equipped_armor["anillo2"].name == "Anillo de Precisión"
    assert loaded_player.equipped_armor["amuleto"].name == "Amuleto de Resistencia"
    assert loaded_player.equipped_armor["peto"] is None
    assert loaded_player.enemy_kill_counts == {"Goblin": 3, "Esqueleto": 1}


def test_load_recognizes_player_by_registered_name_ignoring_case(tmp_save_dir):
    """La partida se creó como "Guille"; al cargar escribiendo "guille" debe
    encontrarla y, además, el personaje pasa a llamarse "Guille" (nombre
    canónico), no lo que se tecleó en el prompt."""
    save_game(_build_player("Guille"), unlocked_enemies=["Goblin"], defeated_enemies=[])

    loaded_player = Player("guille", Stats(1, 1, 1, 1, 1))
    result = load_game(loaded_player)

    assert result is not None
    assert result[0] == "Guille"
    assert loaded_player.name == "Guille"


def test_save_exists_matches_registered_name_ignoring_case(tmp_save_dir):
    """start_new_game usa esto para no dejar crear "guille" si ya existe "Guille"."""
    assert save_exists("Guille") is False

    save_game(_build_player("Guille"), unlocked_enemies=["Goblin"], defeated_enemies=[])

    assert save_exists("Guille") is True
    assert save_exists("guille") is True
    assert save_exists("GUILLE") is True
    assert save_exists("Otro") is False


def test_load_backfills_kill_count_for_legacy_saves_without_the_field(tmp_save_dir):
    """Partidas guardadas antes de contar derrotas: al menos 1 por cada enemigo ya derrotado."""
    legacy_save_data = {
        "player_name": "Guille",
        "unlocked_enemies": ["Goblin", "Esqueleto"],
        "defeated_enemies": ["Goblin"],
        "gold": 10,
        "player_stats": {
            "level": 1,
            "experience": 0,
            "health": 100,
            "max_health": 100,
            "min_atk": 5,
            "max_atk": 10,
            "armor": 2,
            "magic_resist": 0,
        },
        "inventory": [],
        "inventory_quantities": {},
        "equipped_weapon": None,
        "equipped_armor": None,
        # sin "enemy_kill_counts"
    }
    encoded = base64.b64encode(json.dumps(legacy_save_data).encode("utf-8"))
    (tmp_save_dir / "Guille.sav").write_bytes(encoded)

    loaded_player = Player("Guille", Stats(1, 1, 1, 1, 1))
    result = load_game(loaded_player)

    assert result is not None
    assert loaded_player.enemy_kill_counts == {"Goblin": 1}


def test_save_creates_backup_of_previous_save(tmp_save_dir):
    player = _build_player()
    save_game(player, unlocked_enemies=["Goblin"], defeated_enemies=[])
    player.inventory.gold = 999
    save_game(player, unlocked_enemies=["Goblin"], defeated_enemies=[])

    backup_path = tmp_save_dir / "Guille.bak"
    assert backup_path.exists()


def test_load_falls_back_to_backup_when_main_save_fails_unexpectedly(tmp_save_dir):
    player = _build_player()
    save_game(player, unlocked_enemies=["Goblin"], defeated_enemies=[])  # 1ra vez: crea .sav (sin .bak aún)
    save_game(player, unlocked_enemies=["Goblin"], defeated_enemies=[])  # 2da vez: crea .bak = copia del .sav válido

    sav_path = tmp_save_dir / "Guille.sav"
    bak_path = tmp_save_dir / "Guille.bak"
    assert bak_path.exists()

    # Un JSON válido pero con forma inesperada (lista en vez de dict) provoca un
    # TypeError al indexar save_data["player_stats"], que es lo único que
    # activa la ruta de fallback al backup en load_game().
    corrupt_payload = base64.b64encode(json.dumps([]).encode("utf-8"))
    sav_path.write_bytes(corrupt_payload)

    loaded_player = Player("Guille", Stats(1, 1, 1, 1, 1))
    result = load_game(loaded_player)

    assert result is not None
    assert loaded_player.inventory.gold == 42


def test_load_returns_none_when_no_save_exists(tmp_save_dir):
    loaded_player = Player("Nadie", Stats(1, 1, 1, 1, 1))
    assert load_game(loaded_player) is None


def test_load_restores_from_bak_when_sav_is_missing(tmp_save_dir):
    """Sin .sav pero con .bak, load_game copia el backup y carga desde él."""
    save_game(_build_player(), unlocked_enemies=["Goblin"], defeated_enemies=[])
    save_game(_build_player(), unlocked_enemies=["Goblin"], defeated_enemies=[])  # crea .bak
    (tmp_save_dir / "Guille.sav").unlink()

    result = load_game(Player("Guille", Stats(1, 1, 1, 1, 1)))

    assert result is not None
    assert (tmp_save_dir / "Guille.sav").exists()  # restaurado


def test_load_returns_none_on_corrupt_base64(tmp_save_dir):
    (tmp_save_dir / "Guille.sav").write_bytes(b"esto no es base64 valido !!!")
    assert load_game(Player("Guille", Stats(1, 1, 1, 1, 1))) is None


def test_save_game_reports_serialization_error(tmp_save_dir, capsys):
    player = _build_player()
    player.enemy_kill_counts = {"Goblin": object()}  # no serializable a JSON

    save_game(player, unlocked_enemies=["Goblin"], defeated_enemies=[])

    assert "serialización" in capsys.readouterr().out.lower()
    assert not (tmp_save_dir / "Guille.sav").exists()


def test_check_save_directory_reports_when_it_cannot_be_created(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(save_load, "SAVE_DIR", tmp_path / "no")

    def boom(*a, **k):
        raise OSError("permiso denegado")

    monkeypatch.setattr(save_load.os, "makedirs", boom)
    save_load.check_save_directory()

    assert "No se pudo crear" in capsys.readouterr().out


def test_load_falls_back_on_legacy_defense_key(tmp_save_dir):
    """Partidas guardadas antes de renombrar 'defense' a 'armor' deben poder cargarse igualmente."""
    legacy_save_data = {
        "player_name": "Guille",
        "unlocked_enemies": ["Goblin"],
        "defeated_enemies": [],
        "gold": 10,
        "player_stats": {
            "level": 1,
            "experience": 0,
            "health": 100,
            "max_health": 100,
            "min_atk": 5,
            "max_atk": 10,
            "defense": 2,  # clave antigua, sin "armor" ni "magic_resist"
        },
        "inventory": [],
        "inventory_quantities": {},
        "equipped_weapon": None,
        "equipped_armor": None,
    }
    encoded = base64.b64encode(json.dumps(legacy_save_data).encode("utf-8"))
    (tmp_save_dir / "Guille.sav").write_bytes(encoded)

    loaded_player = Player("Guille", Stats(1, 1, 1, 1, 1))
    result = load_game(loaded_player)

    assert result is not None
    assert loaded_player.stats.armor == 2
    assert loaded_player.stats.magic_resist == 0


def test_load_falls_back_on_legacy_single_equipped_armor(tmp_save_dir):
    """Partidas guardadas antes de los huecos de armadura tenían equipped_armor como un solo objeto."""
    legacy_save_data = {
        "player_name": "Guille",
        "unlocked_enemies": ["Goblin"],
        "defeated_enemies": [],
        "gold": 10,
        "player_stats": {
            "level": 1,
            "experience": 0,
            "health": 100,
            "max_health": 100,
            "min_atk": 5,
            "max_atk": 10,
            "armor": 2,
            "magic_resist": 0,
        },
        "inventory": [],
        "inventory_quantities": {},
        "equipped_weapon": None,
        # Formato antiguo: un solo objeto de armadura (sin "slot"), no un dict de huecos
        "equipped_armor": {"type": "Armor", "name": "Casco Viejo", "description": "desc", "value": 8, "defense": 5},
    }
    encoded = base64.b64encode(json.dumps(legacy_save_data).encode("utf-8"))
    (tmp_save_dir / "Guille.sav").write_bytes(encoded)

    loaded_player = Player("Guille", Stats(1, 1, 1, 1, 1))
    result = load_game(loaded_player)

    assert result is not None
    assert loaded_player.equipped_armor["peto"].name == "Casco Viejo"
    assert all(item is None for slot, item in loaded_player.equipped_armor.items() if slot != "peto")
