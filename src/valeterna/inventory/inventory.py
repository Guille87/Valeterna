from valeterna.items.equipment import Armor, Weapon, slot_accepts, slot_label
from valeterna.items.materials import Material
from valeterna.items.potions.potion_base import Potion
from valeterna.ui import console


class Inventory:
    def __init__(self, player):
        self.items = []  # Lista de objetos únicos
        self.quantities = {}  # { "Poción de Salud": 5 }
        self.gold = 0
        self.player = player  # Guarda una referencia al objeto Player
        self.item_mapping = {}
        # Nombres de Material que el jugador ha conseguido alguna vez, aunque ya
        # no tenga stock (se consuma al craftear). Permanente una vez descubierto;
        # usado por crafting/forge.py para no mostrar recetas de materiales que
        # el jugador nunca ha visto todavía.
        self.discovered_materials = set()

    def add_item(self, item, quantity: int = 1, *, announce: bool = True) -> None:
        """Añade `quantity` unidades de un ítem gestionando stacks para
        consumibles y oro para equipo repetido. Imprime "Obtenido: X" una sola
        vez (con `xN` si son varias), no una línea por unidad."""
        if quantity < 1:
            return
        if isinstance(item, Material):
            self.discovered_materials.add(item.name)

        # Si es equipo (Arma/Armadura), comprobamos si ya existe por nombre
        if isinstance(item, (Weapon, Armor)):
            existing = next((i for i in self.items if i.name == item.name), None)
            if existing:
                self.gold += item.value
                console.warning(f"¡Repetido! Has vendido el {item.name} por {item.value} de oro.")
                return

        # Lógica de Stacking
        if item.name in self.quantities:
            self.quantities[item.name] += quantity
        else:
            self.items.append(item)
            self.quantities[item.name] = quantity

        if announce:
            suffix = f" x{quantity}" if quantity > 1 else ""
            console.success(f"Obtenido: {item.name}{suffix}")

    def load_items(self, items_list: list) -> None:
        """Limpia y carga una lista de objetos reconstruyendo el stacking."""
        self.items = []
        self.quantities = {}
        for item in items_list:
            # Usamos la misma lógica que add_item pero sin prints
            if item.name in self.quantities:
                self.quantities[item.name] += 1
            else:
                self.items.append(item)
                self.quantities[item.name] = 1

    def show_inventory(self, filter_class=None, filter_slot: str | None = None, mode: str = "view") -> bool:
        """
        mode "view": Solo lectura
        mode "use": Permite seleccionar número para usar
        """
        print("\n" + "=" * 45)
        title = "INVENTARIO COMPLETO"
        if filter_class == Weapon:
            title = "SELECCIONAR ARMA"
        elif filter_class == Armor and filter_slot:
            title = f"SELECCIONAR {slot_label(filter_slot).upper()}"
        elif filter_class == Armor:
            title = "SELECCIONAR ARMADURA"

        print(console.colorize(f"--- {title} ---", console.Fore.CYAN))
        print(
            console.colorize(
                f"Vida: {self.player.stats.health}/{self.player.stats.max_health}", console.Fore.GREEN, bright=True
            )
        )

        items_to_show = [
            i
            for i in self.items
            if (not filter_class or isinstance(i, filter_class))
            and (not filter_slot or slot_accepts(filter_slot, getattr(i, "slot", None)))
        ]

        if not items_to_show:
            print("No hay objetos en esta categoría.")
            print("=" * 45)
            return False

        self.item_mapping = {}
        for idx, item in enumerate(items_to_show, 1):
            self.item_mapping[idx] = item
            qty = self.quantities.get(item.name, 1)

            # Formato de línea
            is_equipped = item == self.player.equipped_weapon or item in self.player.equipped_armor.values()
            is_eq = f"{console.colorize('(E)', console.Fore.BLUE)} " if is_equipped else ""
            qty_str = console.colorize(f" x{qty}", console.Fore.YELLOW) if qty > 1 else ""

            material_tag = " (material)" if isinstance(item, Material) else ""
            print(console.tint_status(f"{idx}. {is_eq}{item.name}{qty_str} | {item.description}{material_tag}"))
            stats_info = item.get_stats_info()
            if stats_info:
                print(console.tint_status(f"   [{stats_info}]"))

        print(f"\n{console.colorize(f'Oro: {self.gold}', console.Fore.YELLOW)}")
        print("=" * 45)

        if mode == "use":
            return self._handle_selection(filter_class=filter_class, filter_slot=filter_slot)
        return False

    def _handle_selection(self, filter_class=None, filter_slot: str | None = None) -> bool:
        choice = console.ask("\nSelecciona un número (0 para volver): ")
        if choice == "0" or not choice.isdigit():
            return False

        idx = int(choice)
        item = self.item_mapping.get(idx)

        if item:
            # 1. Caso: Inventario General (filter_class es None)
            if filter_class is None:
                if not isinstance(item, Potion):
                    console.error("Las armas y armaduras se equipan desde sus respectivos menús.")
                    return False

                # 2. Caso: Menú de Equipo específico (filter_class tiene valor)
            else:
                if not isinstance(item, filter_class):
                    console.error("No puedes equipar eso aquí.")
                    return False
                if filter_slot and not slot_accepts(filter_slot, getattr(item, "slot", None)):
                    console.error("Este objeto no va en ese hueco.")
                    return False

            # Si pasa las validaciones, usamos el objeto
            if isinstance(item, Armor):
                success = item.use(self.player, target_slot=filter_slot)
            else:
                success = item.use(self.player)
            if success:
                # Si es un consumible (Poción), restamos cantidad
                if not isinstance(item, (Weapon, Armor)):
                    self._remove_one(item)
                return True
            else:
                # Si success es False, devolvemos False para no cerrar el menú ni gastar turno
                return False
        return False

    def equip_menu(self, filter_class=None, filter_slot: str | None = None) -> bool:
        """Llamado desde las opciones de equipar arma/armadura del menú principal."""
        return self.show_inventory(filter_class=filter_class, filter_slot=filter_slot, mode="use")

    def _remove_one(self, item) -> None:
        """Descuenta una unidad de un ítem del inventario, eliminándolo si llega a 0."""
        self.quantities[item.name] -= 1
        if self.quantities[item.name] <= 0:
            self.items.remove(item)
            del self.quantities[item.name]

    def has_item(self, name: str, quantity: int = 1) -> bool:
        """Comprueba si hay al menos `quantity` unidades de un ítem por nombre."""
        return self.quantities.get(name, 0) >= quantity

    def consume_item(self, name: str, quantity: int = 1) -> bool:
        """Consume `quantity` unidades de un ítem por nombre. Devuelve False si no hay suficientes."""
        if not self.has_item(name, quantity):
            return False
        item = next(i for i in self.items if i.name == name)
        for _ in range(quantity):
            self._remove_one(item)
        return True

    def sell_item(self, item) -> int | None:
        """Vende una unidad del ítem dado a su valor base. Devuelve el oro obtenido, o None si no se puede vender."""
        if item == self.player.equipped_weapon or item in self.player.equipped_armor.values():
            console.error("No puedes vender un objeto equipado.")
            return None

        self._remove_one(item)
        self.gold += item.value
        return item.value

    def load_saved_inventory(self, items_list: list, quantities_dict: dict) -> None:
        """Sincroniza la lista de items con sus cantidades reales al cargar."""
        self.items = items_list
        self.quantities = quantities_dict
