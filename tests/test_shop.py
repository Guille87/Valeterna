import pytest

from valeterna.items.equipment import Weapon
from valeterna.shop.shop import Shop
from valeterna.world.map import ZONE_ORDER


def _answers(monkeypatch, *responses):
    """Encola respuestas para console.ask dentro de shop.py."""
    it = iter(responses)
    monkeypatch.setattr("valeterna.shop.shop.console.ask", lambda prompt: next(it))


def test_buy_with_enough_gold_deducts_price_and_adds_item(player, monkeypatch):
    shop = Shop()
    player.inventory.gold = 100

    monkeypatch.setattr("valeterna.shop.shop.console.ask", lambda prompt: "1")
    shop._buy_menu(player)

    bought = shop.catalog[0]
    assert player.inventory.gold == 100 - bought.buy_price
    assert bought.template.name in player.inventory.quantities


def test_buy_without_enough_gold_does_nothing(player, monkeypatch):
    shop = Shop()
    player.inventory.gold = 0

    monkeypatch.setattr("valeterna.shop.shop.console.ask", lambda prompt: "1")
    shop._buy_menu(player)

    assert player.inventory.gold == 0
    assert player.inventory.items == []


def test_sell_item_from_inventory_grants_gold_and_removes_it(player, monkeypatch):
    shop = Shop()
    weapon = Weapon("Espada Vieja", "desc", value=7, damage=3)
    player.inventory.add_item(weapon)

    monkeypatch.setattr("valeterna.shop.shop.console.ask", lambda prompt: "1")
    shop._sell_menu(player)

    assert player.inventory.gold == 7
    assert weapon not in player.inventory.items


def test_cannot_sell_equipped_item(player, monkeypatch):
    shop = Shop()
    weapon = Weapon("Espada Equipada", "desc", value=7, damage=3)
    player.inventory.add_item(weapon)
    player.equipped_weapon = weapon

    monkeypatch.setattr("valeterna.shop.shop.console.ask", lambda prompt: "1")
    shop._sell_menu(player)

    assert player.inventory.gold == 0
    assert weapon in player.inventory.items


def test_open_loop_buy_then_back(player, monkeypatch):
    """open(): comprar (1) -> volver del submenú -> salir (3)."""
    shop = Shop()
    player.inventory.gold = 100
    # "1" abre comprar, "1" elige el primer objeto, "1" cantidad, "3" sale.
    _answers(monkeypatch, "1", "1", "1", "3")
    shop.open(player)

    assert player.inventory.gold == 100 - shop.catalog[0].buy_price


def test_open_loop_sell_then_back(player, monkeypatch):
    shop = Shop()
    player.inventory.add_item(Weapon("Espada Vieja", "desc", value=7, damage=3))
    _answers(monkeypatch, "2", "1", "3")
    shop.open(player)

    assert player.inventory.gold == 7


def test_open_loop_rejects_invalid_option_then_exits(player, monkeypatch, capsys):
    _answers(monkeypatch, "9", "3")
    Shop().open(player)

    assert "Opción no válida." in capsys.readouterr().out


def test_buy_multiple_of_a_stackable_item(player, monkeypatch):
    shop = Shop()
    player.inventory.gold = 100
    healing = shop.catalog[0]  # Poción de Salud, apilable

    _answers(monkeypatch, "1", "3")  # elige item 1, compra 3
    shop._buy_menu(player)

    assert player.inventory.quantities[healing.template.name] == 3
    assert player.inventory.gold == 100 - healing.buy_price * 3


def test_buy_quantity_is_capped_by_gold(player, monkeypatch):
    shop = Shop()
    player.inventory.gold = 12  # solo llega para 2 pociones de 5
    _answers(monkeypatch, "1", "99")  # pide 99, solo puede 2
    shop._buy_menu(player)

    assert player.inventory.quantities["Poción de Salud"] == 2
    assert player.inventory.gold == 2


def test_sell_multiple_units(player, monkeypatch):
    from valeterna.items.potions.healing_potion import HealingPotion

    shop = Shop()
    for _ in range(4):
        player.inventory.add_item(HealingPotion("Poción de Salud", "desc", 2, 20))

    _answers(monkeypatch, "1", "3")  # vende 3 de 4
    shop._sell_menu(player)

    assert player.inventory.quantities["Poción de Salud"] == 1
    assert player.inventory.gold == 2 * 3


@pytest.mark.parametrize("choice", ["abc", "999", "0"])
def test_buy_menu_handles_bad_input(player, monkeypatch, choice):
    shop = Shop()
    player.inventory.gold = 100
    monkeypatch.setattr("valeterna.shop.shop.console.ask", lambda prompt: choice)
    shop._buy_menu(player)

    assert player.inventory.gold == 100  # nada comprado


def test_visible_items_is_just_the_base_catalog_with_only_piedrablanca_visited(player):
    shop = Shop()
    assert shop._visible_items(player) == shop.catalog


def test_visiting_a_zone_unlocks_its_own_gear_tier(player):
    shop = Shop()
    player.mundo["zonas_visitadas"].append("bosque_de_los_susurros")

    visible = shop._visible_items(player)

    assert visible[: len(shop.catalog)] == shop.catalog
    assert visible[len(shop.catalog) :] == shop.zone_gear["bosque_de_los_susurros"]


def test_unlocked_gear_tiers_follow_zone_order_not_visit_order(player):
    shop = Shop()
    # Se visita el Cañón antes que la Ciénaga (p. ej. viaje rápido tras
    # explorar), pero el catálogo debe listar los escalones en el orden del
    # mapa, no en el orden en que se visitaron.
    player.mundo["zonas_visitadas"] += ["canon_del_trueno", "cienaga_de_los_ahogados"]

    visible = shop._visible_items(player)
    extra_names = [item.template.name for item in visible[len(shop.catalog) :]]
    expected_names = [item.template.name for item in shop.zone_gear["cienaga_de_los_ahogados"]] + [
        item.template.name for item in shop.zone_gear["canon_del_trueno"]
    ]
    assert extra_names == expected_names


def test_every_zone_gear_tier_stays_below_that_zones_own_first_real_weapon_drop():
    """Cada arma de tienda debe quedar por debajo (nunca igualar o superar) el
    primer drop real de arma de esa zona, para que sea un colchón de
    emergencia y no un atajo mejor que jugar."""
    from valeterna.items.equipment import Weapon
    from valeterna.ui.menus import _get_enemy_instance
    from valeterna.world.map import ZONES

    shop = Shop()
    for zone_id, items in shop.zone_gear.items():
        zone = ZONES[zone_id]
        first_enemy = _get_enemy_instance(zone.enemies[0])
        first_weapon_damage = next(item.damage for item, _prob in first_enemy.drop_table() if isinstance(item, Weapon))
        for shop_item in items:
            if isinstance(shop_item.template, Weapon):
                assert shop_item.template.damage < first_weapon_damage, (
                    f"{shop_item.template.name} ({zone_id}) iguala o supera el primer drop de la zona"
                )


def test_zone_gear_price_increases_along_zone_order():
    shop = Shop()
    zones_with_gear = [zone_id for zone_id in ZONE_ORDER if zone_id in shop.zone_gear]
    prices = [shop.zone_gear[zone_id][0].buy_price for zone_id in zones_with_gear]
    assert prices == sorted(prices)
    assert len(set(prices)) == len(prices)
