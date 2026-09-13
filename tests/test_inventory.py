from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions.buff_potion import StatBuffPotion
from valeterna.items.potions.healing_potion import HealingPotion
from valeterna.items.potions.regen_potion import RegenPotion


def test_add_item_stacks_consumables(player):
    potion = HealingPotion("Poción de Salud", "desc", 2, 20)
    player.inventory.add_item(potion)
    player.inventory.add_item(HealingPotion("Poción de Salud", "desc", 2, 20))

    assert len(player.inventory.items) == 1
    assert player.inventory.quantities["Poción de Salud"] == 2


def test_add_item_auto_sells_duplicate_equipment(player):
    weapon = Weapon("Espada Goblin", "desc", value=5, damage=4)
    player.inventory.add_item(weapon)
    player.inventory.add_item(Weapon("Espada Goblin", "desc", value=5, damage=4))

    assert len(player.inventory.items) == 1
    assert player.inventory.gold == 5


def test_equip_menu_equips_selected_weapon(player, monkeypatch):
    weapon = Weapon("Espada Goblin", "desc", value=5, damage=4)
    player.inventory.add_item(weapon)

    monkeypatch.setattr("valeterna.inventory.inventory.console.ask", lambda prompt: "1")
    used = player.inventory.equip_menu(Weapon)

    assert used is True
    assert player.equipped_weapon is weapon


def test_equip_menu_rejects_wrong_category(player, monkeypatch):
    player.inventory.add_item(Armor("Casco", "desc", value=8, slot="casco", defense=5))

    monkeypatch.setattr("valeterna.inventory.inventory.console.ask", lambda prompt: "1")
    used = player.inventory.equip_menu(Weapon)

    assert used is False
    assert player.equipped_weapon is None


def test_equip_menu_with_filter_slot_equips_into_correct_slot(player, monkeypatch):
    casco = Armor("Casco de Hueso", "desc", value=8, slot="casco", max_health=15)
    player.inventory.add_item(casco)

    monkeypatch.setattr("valeterna.inventory.inventory.console.ask", lambda prompt: "1")
    used = player.inventory.equip_menu(Armor, filter_slot="casco")

    assert used is True
    assert player.equipped_armor["casco"] is casco


def test_equip_menu_with_filter_slot_rejects_item_from_other_slot(player, monkeypatch):
    guantes = Armor("Guantes", "desc", value=8, slot="guantes")
    player.inventory.add_item(guantes)

    monkeypatch.setattr("valeterna.inventory.inventory.console.ask", lambda prompt: "1")
    used = player.inventory.equip_menu(Armor, filter_slot="casco")  # el jugador solo tiene guantes

    assert used is False
    assert player.equipped_armor["casco"] is None


def test_sell_item_blocks_any_equipped_armor_slot(player, monkeypatch):
    peto = Armor("Peto", "desc", value=8, slot="peto")
    player.inventory.add_item(peto)

    monkeypatch.setattr("valeterna.inventory.inventory.console.ask", lambda prompt: "1")
    player.inventory.equip_menu(Armor, filter_slot="peto")

    assert player.inventory.sell_item(peto) is None
    assert player.equipped_armor["peto"] is peto


def test_can_equip_two_different_rings_at_once(player, monkeypatch):
    anillo1 = Armor("Anillo de Fuerza", "desc", value=16, slot="anillo", damage=3)
    anillo2 = Armor("Anillo de Precisión", "desc", value=20, slot="anillo", crit_damage=0.12)
    player.inventory.add_item(anillo1)
    player.inventory.add_item(anillo2)

    # Ambos anillos siguen apareciendo en el listado tras el primer equipar (no se consumen),
    # así que elegimos por posición: "1" -> Anillo de Fuerza, "2" -> Anillo de Precisión.
    monkeypatch.setattr("valeterna.inventory.inventory.console.ask", lambda prompt: "1")
    used1 = player.inventory.equip_menu(Armor, filter_slot="anillo1")

    monkeypatch.setattr("valeterna.inventory.inventory.console.ask", lambda prompt: "2")
    used2 = player.inventory.equip_menu(Armor, filter_slot="anillo2")

    assert used1 is True
    assert used2 is True
    assert player.equipped_armor["anillo1"] is anillo1
    assert player.equipped_armor["anillo2"] is anillo2


def test_ring_rejected_in_non_ring_slot(player, monkeypatch):
    anillo = Armor("Anillo de Fuerza", "desc", value=16, slot="anillo", damage=3)
    player.inventory.add_item(anillo)

    monkeypatch.setattr("valeterna.inventory.inventory.console.ask", lambda prompt: "1")
    used = player.inventory.equip_menu(Armor, filter_slot="casco")

    assert used is False
    assert player.equipped_armor["casco"] is None


def test_non_ring_item_rejected_in_ring_slot(player, monkeypatch):
    casco = Armor("Casco", "desc", value=8, slot="casco")
    player.inventory.add_item(casco)

    monkeypatch.setattr("valeterna.inventory.inventory.console.ask", lambda prompt: "1")
    used = player.inventory.equip_menu(Armor, filter_slot="anillo1")

    assert used is False
    assert player.equipped_armor["anillo1"] is None


def test_get_stats_info_available_on_every_item_type():
    """Todo objeto que puede acabar en el inventario debe exponer get_stats_info()
    porque show_inventory() lo llama al listar. Un Material lo hereda vacío de Item;
    olvidarlo hacía crashear el inventario al recoger cualquier material."""
    items = [
        HealingPotion("Poción de Salud", "desc", 2, 20),
        RegenPotion("Poción de Regeneración", "desc", 5, 3, 3),
        StatBuffPotion("Poción de Fuerza", "desc", 5, "min_atk", 5, 3),
        Weapon("Espada", "desc", value=5, damage=4),
        Armor("Casco", "desc", value=8, slot="casco", max_health=15),
        Material("Colmillo de Goblin", "desc", 1),
    ]
    for item in items:
        assert isinstance(item.get_stats_info(), str)

    assert Material("Colmillo de Goblin", "desc", 1).get_stats_info() == ""


def test_show_inventory_renders_mixed_bag_without_crashing(player, capsys):
    """Regresión: abrir el inventario con una mezcla de pociones, arma, armadura
    y material no debe lanzar ninguna excepción (antes crasheaba en el material)."""
    player.inventory.add_item(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20))
    player.inventory.add_item(RegenPotion("Poción de Regeneración", "Regenera HP", 5, 3, 3))
    player.inventory.add_item(Weapon("Espada Goblin", "Un arma tosca", value=5, damage=4))
    player.inventory.add_item(Armor("Casco de Hueso", "Un casco", value=8, slot="casco", max_health=15))
    player.inventory.add_item(Material("Colmillo de Goblin", "Un colmillo curvo y afilado", 1))
    player.inventory.add_item(Material("Piel de Troll", "Piel imperecedera", 5))

    player.inventory.show_inventory()

    out = capsys.readouterr().out
    assert "Colmillo de Goblin" in out
    assert "Piel de Troll" in out
    # El material no debe imprimir una línea de stats vacía "[]".
    assert "[]" not in out


def test_using_healing_potion_heals_and_consumes_one(player, monkeypatch):
    player.inventory.add_item(HealingPotion("Poción de Salud", "desc", 2, 20))
    player.stats.health = 50

    monkeypatch.setattr("valeterna.inventory.inventory.console.ask", lambda prompt: "1")
    used = player.inventory.equip_menu()  # filter_class=None -> inventario general

    assert used is True
    assert player.stats.health == 70
    assert "Poción de Salud" not in player.inventory.quantities
    assert player.inventory.items == []


def test_using_stat_buff_potion_in_combat_consumes_one_from_stack(player, monkeypatch):
    player.in_combat = True
    player.inventory.add_item(StatBuffPotion("Poción de Fuerza", "desc", 5, "max_atk", 5, 3))

    monkeypatch.setattr("valeterna.inventory.inventory.console.ask", lambda prompt: "1")
    used = player.inventory.equip_menu()

    assert used is True
    assert "Poción de Fuerza" not in player.inventory.quantities
    assert player.inventory.items == []
    assert len(player.active_effects) == 1


def test_has_item_checks_quantity(player):
    player.inventory.add_item(HealingPotion("Poción de Salud", "desc", 2, 20))
    player.inventory.add_item(HealingPotion("Poción de Salud", "desc", 2, 20))

    assert player.inventory.has_item("Poción de Salud", 2) is True
    assert player.inventory.has_item("Poción de Salud", 3) is False
    assert player.inventory.has_item("Objeto Inexistente") is False


def test_consume_item_removes_quantity_and_entry_when_empty(player):
    player.inventory.add_item(HealingPotion("Poción de Salud", "desc", 2, 20))
    player.inventory.add_item(HealingPotion("Poción de Salud", "desc", 2, 20))

    assert player.inventory.consume_item("Poción de Salud", 2) is True
    assert "Poción de Salud" not in player.inventory.quantities
    assert player.inventory.items == []


def test_consume_item_fails_without_enough_quantity(player):
    player.inventory.add_item(HealingPotion("Poción de Salud", "desc", 2, 20))

    assert player.inventory.consume_item("Poción de Salud", 2) is False
    assert player.inventory.quantities["Poción de Salud"] == 1
