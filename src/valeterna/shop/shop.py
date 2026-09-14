from valeterna.items.equipment import Armor, Weapon
from valeterna.items.factory import item_factory
from valeterna.items.potions.antidote_potion import AntidotePotion
from valeterna.items.potions.buff_potion import StatBuffPotion
from valeterna.items.potions.healing_potion import HealingPotion
from valeterna.items.potions.potion_base import Potion
from valeterna.items.potions.regen_potion import RegenPotion
from valeterna.ui import console


def _gold(amount) -> str:
    return console.colorize(f"{amount} oro", console.Fore.YELLOW, bright=True)


def _item_name(item) -> str:
    """Nombre del objeto coloreado por tipo (arma por su elemento, armadura azul,
    consumible verde, material gris)."""
    if isinstance(item, Weapon):
        return console.colorize(item.name, console.element_color(item.element))
    if isinstance(item, Armor):
        return console.colorize(item.name, console.Fore.BLUE, bright=True)
    if isinstance(item, Potion):
        return console.colorize(item.name, console.Fore.GREEN)
    return console.colorize(item.name, console.Fore.LIGHTBLACK_EX)


def _ask_quantity(available: int) -> int:
    """Pregunta cuántas unidades (1..available). Si se pide de más, se ajusta a
    `available`. 0 o entrada no válida -> 0 (cancela)."""
    if available <= 1:
        return available
    raw = console.ask(f"¿Cuántas? (máx. {available}, 0 para cancelar): ")
    if not raw.isdigit():
        return 0
    return max(0, min(int(raw), available))


class ShopItem:
    """Una entrada del catálogo: una plantilla de ítem y su precio de compra."""

    def __init__(self, template, buy_price: int):
        self.template = template
        self.buy_price = buy_price

    @property
    def stackable(self) -> bool:
        return not isinstance(self.template, (Weapon, Armor))

    def create_item(self):
        """Crea una copia independiente de la plantilla para entregar al jugador."""
        return item_factory(self.template.to_dict())

    def __str__(self) -> str:
        return console.tint_status(
            f"{_item_name(self.template)} - Compra: {_gold(self.buy_price)} | {self.template.description} "
            f"| [{self.template.get_stats_info()}]"
        )


class Shop:
    def __init__(self):
        self.catalog = [
            ShopItem(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20), buy_price=5),
            ShopItem(
                RegenPotion(
                    "Poción de Regeneración", "Un brebaje verde que burbujea. Cura 10 HP durante 3 turnos.", 8, 10, 3
                ),
                buy_price=18,
            ),
            ShopItem(
                StatBuffPotion("Poción de Fuerza", "Aumenta el ataque temporalmente", 5, "max_atk", 5, 3), buy_price=12
            ),
            ShopItem(
                AntidotePotion(
                    "Antídoto", "Purga veneno, quemadura, parálisis, congelación y combustión al instante.", 6
                ),
                buy_price=15,
            ),
            ShopItem(
                Weapon("Espada de Hierro", "Una espada bien forjada, superior a las improvisadas", 10, damage=6),
                buy_price=25,
            ),
            ShopItem(
                Armor("Armadura de Cuero", "Protección ligera pero fiable", 10, slot="peto", defense=4, max_health=10),
                buy_price=25,
            ),
        ]

    def open(self, player) -> None:
        """Punto de entrada del menú interactivo de la tienda."""
        while True:
            print(console.colorize("\n--- TIENDA ---", console.Fore.YELLOW, bright=True))
            print(f"Oro disponible: {_gold(player.inventory.gold)}")
            print(f"{console.colorize('1.', console.Fore.CYAN)} Comprar")
            print(f"{console.colorize('2.', console.Fore.CYAN)} Vender")
            print(f"{console.colorize('3.', console.Fore.CYAN)} Volver")

            choice = console.ask("\nSelecciona una opción: ")
            if choice == "1":
                self._buy_menu(player)
            elif choice == "2":
                self._sell_menu(player)
            elif choice == "3":
                break
            else:
                console.error("Opción no válida.")

    def _buy_menu(self, player) -> None:
        if not self.catalog:
            print("No hay objetos en venta.")
            return

        print(console.colorize("\n--- OBJETOS EN VENTA ---", console.Fore.CYAN, bright=True))
        for idx, shop_item in enumerate(self.catalog, 1):
            print(f"{console.colorize(f'{idx}.', console.Fore.CYAN)} {shop_item}")
        print(f"{console.colorize(f'{len(self.catalog) + 1}.', console.Fore.CYAN)} Volver")

        choice = console.ask(f"\nElige qué comprar (1-{len(self.catalog) + 1}): ")
        if not choice.isdigit():
            console.error("Entrada no válida.")
            return

        idx = int(choice) - 1
        if idx == len(self.catalog):
            return
        if not (0 <= idx < len(self.catalog)):
            console.error("Opción fuera de rango.")
            return

        shop_item = self.catalog[idx]
        if player.inventory.gold < shop_item.buy_price:
            console.error("No tienes suficiente oro ni para una unidad.")
            return

        # Consumibles: se compran varios a la vez, hasta lo que permita el oro.
        # Armas/armaduras: siempre una.
        max_affordable = player.inventory.gold // shop_item.buy_price
        quantity = _ask_quantity(max_affordable) if shop_item.stackable else 1
        if quantity <= 0:
            return

        total = shop_item.buy_price * quantity
        player.inventory.gold -= total
        player.inventory.add_item(shop_item.create_item(), quantity, announce=False)
        unidades = f"{quantity}x " if quantity > 1 else ""
        console.success(f"Has comprado {unidades}{shop_item.template.name} por {total} oro.")

    def _sell_menu(self, player) -> None:
        items = player.inventory.items
        if not items:
            print("No tienes objetos para vender.")
            return

        print(console.colorize("\n--- VENDER OBJETOS ---", console.Fore.CYAN, bright=True))
        for idx, item in enumerate(items, 1):
            qty = player.inventory.quantities.get(item.name, 1)
            qty_str = console.colorize(f" x{qty}", console.Fore.YELLOW) if qty > 1 else ""
            print(
                f"{console.colorize(f'{idx}.', console.Fore.CYAN)} {_item_name(item)}{qty_str} · vale {_gold(item.value)}"
            )
        print(f"{console.colorize(f'{len(items) + 1}.', console.Fore.CYAN)} Volver")

        choice = console.ask(f"\nElige qué vender (1-{len(items) + 1}): ")
        if not choice.isdigit():
            console.error("Entrada no válida.")
            return

        idx = int(choice) - 1
        if idx == len(items):
            return
        if not (0 <= idx < len(items)):
            console.error("Opción fuera de rango.")
            return

        item = items[idx]
        available = player.inventory.quantities.get(item.name, 1)
        quantity = _ask_quantity(available)
        if quantity <= 0:
            return

        gained = 0
        for _ in range(quantity):
            result = player.inventory.sell_item(item)
            if result is None:  # equipado -> no se puede vender
                break
            gained += result
        if gained:
            unidades = f"{quantity}x " if quantity > 1 else ""
            console.success(f"Has vendido {unidades}{item.name} por {gained} oro.")
