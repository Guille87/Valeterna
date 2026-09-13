import pytest

from valeterna.items.equipment import Armor, Weapon
from valeterna.items.factory import item_factory
from valeterna.items.materials import Material
from valeterna.items.potions.antidote_potion import AntidotePotion
from valeterna.items.potions.buff_potion import StatBuffPotion
from valeterna.items.potions.healing_potion import HealingPotion
from valeterna.items.potions.regen_potion import RegenPotion

ITEM_SAMPLES = [
    Weapon("Espada", "desc", 5, damage=4),
    Weapon("Espada Flamígera", "desc", 15, damage=10, element="fuego"),
    Armor("Casco", "desc", 8, slot="casco", defense=5),
    Armor("Armadura Regenerativa", "desc", 60, slot="peto", defense=14, max_health=35),
    Armor("Guantes de Combate", "desc", 15, slot="guantes", crit_chance=0.05, crit_damage=0.15),
    Armor("Brazales Arcanos", "desc", 25, slot="brazales", magic_resist=3, element="fuego"),
    Armor("Anillo de Fuerza", "desc", 16, slot="anillo", damage=3),
    Armor("Amuleto de Resistencia", "desc", 28, slot="amuleto", defense=2, magic_resist=5),
    Armor("Anillo de Vitalidad", "desc", 14, slot="anillo", regen=2),
    Armor("Botas Ligeras", "desc", 10, slot="botas", crit_damage=0.10, speed=3),
    HealingPotion("Poción de Salud", "desc", 2, heal_amount=20),
    StatBuffPotion("Poción de Fuerza", "desc", 5, stat_name="max_atk", boost=5, duration=3),
    RegenPotion("Poción de Regeneración", "desc", 8, regen_amount=10, duration=3),
    AntidotePotion("Antídoto", "desc", 6),
    Material("Piel de Troll", "desc", 150, rarity="Legendario"),
]


@pytest.mark.parametrize("item", ITEM_SAMPLES, ids=lambda i: type(i).__name__)
def test_item_round_trips_through_factory(item):
    rebuilt = item_factory(item.to_dict())

    assert type(rebuilt) is type(item)
    assert rebuilt.name == item.name
    assert rebuilt.to_dict() == item.to_dict()


def test_item_factory_returns_none_for_unknown_type():
    assert item_factory({"type": "NoExiste"}) is None


def test_item_factory_returns_none_for_empty_data():
    assert item_factory(None) is None
    assert item_factory({}) is None
