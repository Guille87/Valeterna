from valeterna.items.equipment import Armor, Weapon
from valeterna.items.factory import item_factory
from valeterna.items.potions.antidote_potion import AntidotePotion
from valeterna.items.potions.buff_potion import StatBuffPotion
from valeterna.items.potions.healing_potion import HealingPotion
from valeterna.items.potions.potion_base import Potion
from valeterna.items.potions.regen_potion import RegenPotion
from valeterna.ui import console
from valeterna.world.map import ZONE_ORDER


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
    # Equipo adicional que se desbloquea al visitar cada zona (además del
    # catálogo base, siempre disponible desde Piedrablanca). Cada pieza se
    # queda deliberadamente por debajo del primer drop real de esa zona (ver
    # docs/design/enemigos_drops.csv) — es un colchón de emergencia si no ha
    # caído nada mejor todavía, no un atajo para saltarse la progresión.
    # Los Yermos no tiene escalón propio: su nivel ya lo cubre el catálogo
    # base (Espada de Hierro / Armadura de Cuero).
    _ZONE_GEAR: dict[str, list[tuple]] = {
        "bosque_de_los_susurros": [
            (Weapon("Espada de Acero", "Una hoja fabricada en serie, sin filo excepcional pero fiable.", 20, 7), 40),
            (
                Armor(
                    "Peto de Cuero Reforzado",
                    "Cuero grueso con refuerzos metálicos.",
                    20,
                    slot="peto",
                    defense=4,
                    max_health=12,
                ),
                40,
            ),
        ],
        "cienaga_de_los_ahogados": [
            (Weapon("Espada Larga", "Más alcance que una espada corta, y un filo bien cuidado.", 30, 10), 70),
            (
                Armor(
                    "Peto de Placas",
                    "Placas remachadas sobre cota de malla.",
                    30,
                    slot="peto",
                    defense=6,
                    max_health=16,
                ),
                70,
            ),
        ],
        "canon_del_trueno": [
            (Weapon("Mandoble", "Requiere las dos manos, pero el golpe compensa el peso.", 45, 14), 110),
            (
                Armor(
                    "Peto Acorazado",
                    "Metal grueso, pensado para aguantar más que para lucirse.",
                    45,
                    slot="peto",
                    defense=9,
                    max_health=20,
                ),
                110,
            ),
        ],
        "torre_de_los_arcanos": [
            (Weapon("Espada Encantada", "Un herrero de la Torre grabó runas menores en el filo.", 65, 18), 160),
            (
                Armor(
                    "Peto Grabado",
                    "Runas menores repartidas por toda la coraza.",
                    65,
                    slot="peto",
                    defense=11,
                    max_health=24,
                ),
                160,
            ),
        ],
        "ciudadela_en_ruinas": [
            (Weapon("Espada de Campeón", "Forjada para alguien que ya no la necesitó.", 90, 22), 220),
            (
                Armor(
                    "Peto de Campeón",
                    "Perteneció a alguien que resistió más de lo esperado.",
                    90,
                    slot="peto",
                    defense=14,
                    max_health=28,
                ),
                220,
            ),
        ],
        "corazon_de_la_brecha": [
            (Weapon("Espada Legendaria", "El último encargo de un herrero que ya no forja.", 120, 26), 300),
            (
                Armor(
                    "Peto Legendario",
                    "La última armadura que un herrero se atrevió a firmar.",
                    120,
                    slot="peto",
                    defense=17,
                    max_health=32,
                ),
                300,
            ),
        ],
    }

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
                Weapon(
                    "Espada de Hierro",
                    "Una espada sencilla, fabricada en serie; fácil de conseguir, pero nada especial.",
                    4,
                    damage=1,
                ),
                buy_price=15,
            ),
            ShopItem(
                Armor("Armadura de Cuero", "Protección ligera pero fiable", 6, slot="peto", defense=2, max_health=5),
                buy_price=15,
            ),
        ]
        self.zone_gear = {
            zone_id: [ShopItem(template, buy_price=price) for template, price in entries]
            for zone_id, entries in self._ZONE_GEAR.items()
        }

    def _visible_items(self, player) -> list:
        """Catálogo base + el escalón de cada zona ya visitada, en el orden del
        mapa (no en el orden en que se visitaron)."""
        visited = player.mundo.get("zonas_visitadas", [])
        items = list(self.catalog)
        for zone_id in ZONE_ORDER:
            if zone_id in visited:
                items.extend(self.zone_gear.get(zone_id, []))
        return items

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
        items = self._visible_items(player)
        if not items:
            print("No hay objetos en venta.")
            return

        print(console.colorize("\n--- OBJETOS EN VENTA ---", console.Fore.CYAN, bright=True))
        for idx, shop_item in enumerate(items, 1):
            print(f"{console.colorize(f'{idx}.', console.Fore.CYAN)} {shop_item}")
        print(f"{console.colorize(f'{len(items) + 1}.', console.Fore.CYAN)} Volver")

        choice = console.ask(f"\nElige qué comprar (1-{len(items) + 1}): ")
        if not choice.isdigit():
            console.error("Entrada no válida.")
            return

        idx = int(choice) - 1
        if idx == len(items):
            return
        if not (0 <= idx < len(items)):
            console.error("Opción fuera de rango.")
            return

        shop_item = items[idx]
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
            is_equipped = item == player.equipped_weapon or item in player.equipped_armor.values()
            is_eq = f"{console.colorize('(E)', console.Fore.BLUE)} " if is_equipped else ""
            print(
                f"{console.colorize(f'{idx}.', console.Fore.CYAN)} {is_eq}{_item_name(item)}{qty_str} · "
                f"vale {_gold(item.value)}"
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
