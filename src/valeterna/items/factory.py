"""Reconstrucción de ítems a partir de datos serializados (JSON de guardado)."""

from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions.antidote_potion import AntidotePotion
from valeterna.items.potions.buff_potion import StatBuffPotion
from valeterna.items.potions.healing_potion import HealingPotion
from valeterna.items.potions.regen_potion import RegenPotion
from valeterna.ui import console

_ITEM_CLASSES = {
    "HealingPotion": HealingPotion,
    "StatBuffPotion": StatBuffPotion,
    "RegenPotion": RegenPotion,
    "AntidotePotion": AntidotePotion,
    "Material": Material,
    "Weapon": Weapon,
    "Armor": Armor,
}


def item_factory(data: dict):
    """Crea el objeto correcto basado en el diccionario."""
    if not data or not isinstance(data, dict):
        return None

    tipo = data.get("type")
    if tipo in _ITEM_CLASSES:
        try:
            return _ITEM_CLASSES[tipo].from_dict(data)
        except Exception as e:
            console.error(f"Error al reconstruir {tipo}: {e}")
            return None
    return None


# Importado aquí abajo para evitar el ciclo con potion_base (Potion es la base).
from valeterna.items.potions.potion_base import Potion  # noqa: E402


def item_kind_label(item) -> str:
    """Etiqueta corta del tipo de objeto para las listas de botín:
    `arma` / `arma · fuego`, `armadura · casco`, `poción`, `material de herrería`."""
    from valeterna.items.equipment import slot_label

    if isinstance(item, Weapon):
        return f"arma · {item.element}" if item.element else "arma"
    if isinstance(item, Armor):
        return f"armadura · {slot_label(item.slot).lower()}"
    if isinstance(item, Potion):
        return "poción"
    if isinstance(item, Material):
        return "material de herrería"
    return "objeto"
