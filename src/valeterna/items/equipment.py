from valeterna.items.item_base import Item
from valeterna.ui import console

ARMOR_SLOTS = [
    "casco",
    "hombreras",
    "peto",
    "brazales",
    "guantes",
    "cinturon",
    "perneras",
    "botas",
    "anillo1",
    "anillo2",
    "amuleto",
]
RING_SLOTS = ["anillo1", "anillo2"]
SLOT_LABELS = {"anillo1": "Anillo 1", "anillo2": "Anillo 2", "amuleto": "Amuleto"}


def slot_accepts(filter_slot: str, item_slot: str | None) -> bool:
    """¿Puede un ítem con item_slot equiparse en el hueco filter_slot?"""
    if filter_slot in RING_SLOTS:
        return item_slot == "anillo"
    return item_slot == filter_slot


def slot_label(slot: str) -> str:
    """Etiqueta legible de un hueco (los que no están en SLOT_LABELS solo se capitalizan)."""
    return SLOT_LABELS.get(slot, slot.capitalize())


# Probabilidad / duración por defecto del estado que infligen las armas
# elementales que no lo especifican (GDD §6.4).
_DEFAULT_INFLICT_CHANCE = 0.25
_DEFAULT_INFLICT_DURATION = 3


class Weapon(Item):
    def __init__(
        self,
        name: str,
        description: str,
        value: int,
        damage: int,
        element: str | None = None,
        inflicts: dict | None = None,
    ):
        super().__init__(name, description, value)
        self.damage = damage
        self.element = element
        # `inflicts`: {"status", "chance", "duration", "power"}. Si es None y el
        # arma tiene un elemento con estado asociado, se deriva uno por defecto.
        self.inflicts = inflicts

    def get_inflicts(self) -> dict | None:
        """El estado alterado que inflige este golpe, explícito o derivado del
        elemento. `None` si el arma no inflige nada."""
        if self.inflicts:
            return self.inflicts
        from valeterna.combat.elements import ELEMENT_STATUS

        status = ELEMENT_STATUS.get(self.element or "")
        if not status:
            return None
        return {
            "status": status,
            "chance": _DEFAULT_INFLICT_CHANCE,
            "duration": _DEFAULT_INFLICT_DURATION,
            "power": 0,
        }

    def use(self, player) -> bool:
        player.equipped_weapon = self
        print(f"Has equipado {self.name}. (+{self.damage} ATK)")
        return True

    def get_stats_info(self) -> str:
        info = f"Daño: {self.damage}"
        if self.element:
            info += f" ({self.element.capitalize()})"
        inflicts = self.get_inflicts()
        if inflicts:
            from valeterna.i18n import t

            info += f" · inflige {t('status.' + inflicts['status'])} {int(inflicts['chance'] * 100)}%"
        # Un arma elemental se muestra en el color de su elemento; una normal, en rojo.
        return console.colorize(info, console.element_color(self.element))

    def to_dict(self) -> dict:
        # Aseguramos que el daño se guarde con la llave correcta
        data = super().to_dict()
        data.update({"damage": self.damage, "element": self.element, "inflicts": self.inflicts, "type": "Weapon"})
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Weapon":
        return cls(
            name=data["name"],
            description=data["description"],
            value=data["value"],
            damage=data.get("damage", 0),  # Parámetro extra de Weapon
            element=data.get("element"),
            inflicts=data.get("inflicts"),
        )


class Armor(Item):
    def __init__(
        self,
        name: str,
        description: str,
        value: int,
        slot: str,
        defense: int = 0,
        max_health: int = 0,
        magic_resist: int = 0,
        crit_chance: float = 0.0,
        crit_damage: float = 0.0,
        damage: int = 0,
        element: str | None = None,
        regen: int = 0,
        speed: int = 0,
        precision: int = 0,
        evasion: int = 0,
        resist: dict | None = None,
    ):
        super().__init__(name, description, value)
        self.slot = slot
        self.defense = defense
        self.max_health = max_health
        self.magic_resist = magic_resist
        self.crit_chance = crit_chance
        self.crit_damage = crit_damage
        self.damage = damage
        self.element = element
        # Regeneración de salud: sumada en Player.get_total_regen() y aplicada
        # cada turno en Player.on_turn_start(), no se consigue de otra forma
        # (el jugador no sube esta stat al subir de nivel).
        self.regen = regen
        # Velocidad: sumada en Player.get_total_speed(). En la práctica solo las
        # botas la llevan (decisión de diseño, no una restricción del código).
        self.speed = speed
        # Precisión/Evasión: sumadas en Player.get_total_precision()/get_total_evasion().
        # Cada hueco de armadura tiene un "stat base" garantizado que reparte
        # entre todos sus objetos (ver characters/enemies/*::drop_item()); para
        # hombreras es precisión y para perneras es evasión.
        self.precision = precision
        self.evasion = evasion
        # Resistencia elemental (GDD §5): % de reducción de daño por elemento
        # ({"sagrado": 0.1, ...}), sumada en Player.get_total_resist(element) y
        # aplicada en Player.take_damage() antes de la mitigación por
        # armadura/resistencia mágica. Independiente de la afinidad de los
        # enemigos (débil/resiste/inmune): esto es la defensa del jugador.
        self.resist = resist or {}

    def use(self, player, target_slot: str | None = None) -> bool:
        # target_slot lo indica quien equipa (necesario para los anillos: self.slot
        # es solo la categoría "anillo", no una clave real de equipped_armor)
        slot = target_slot or self.slot

        # Si ya había una pieza en este hueco, revertimos su bonus de vida antes de aplicar el nuevo
        old_item = player.equipped_armor.get(slot)
        if old_item:
            player.stats.max_health -= old_item.max_health

        player.equipped_armor[slot] = self
        player.stats.max_health += self.max_health
        player.stats.health = player.stats.health  # re-dispara el clamp del setter por si el máximo bajó

        print(f"Has equipado {self.name}. ({self.get_stats_info()})")
        return True

    def get_stats_info(self) -> str:
        parts = []
        if self.defense:
            parts.append(f"Armadura: {self.defense}")
        if self.max_health:
            parts.append(f"Vida: +{self.max_health}")
        if self.magic_resist:
            parts.append(f"Res.Mágica: {self.magic_resist}")
        if self.crit_chance:
            parts.append(f"Prob.Crítico: +{self.crit_chance * 100:.0f}%")
        if self.crit_damage:
            parts.append(f"Daño Crítico: +{self.crit_damage * 100:.0f}%")
        if self.damage:
            parts.append(f"Daño: +{self.damage}")
        if self.element:
            parts.append(f"Elemento: {self.element.capitalize()}")
        if self.regen:
            parts.append(f"Regeneración: +{self.regen} HP/turno")
        if self.speed:
            parts.append(f"Velocidad: +{self.speed}")
        if self.precision:
            parts.append(f"Precisión: +{self.precision}")
        if self.evasion:
            parts.append(f"Evasión: +{self.evasion}")
        if self.resist:
            resist_str = ", ".join(f"{elem.capitalize()} +{pct * 100:.0f}%" for elem, pct in self.resist.items())
            parts.append(f"Resistencia: {resist_str}")
        info = " | ".join(parts) if parts else "Sin bonus"
        return console.colorize(info, console.Fore.BLUE)

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update(
            {
                "slot": self.slot,
                "defense": self.defense,
                "max_health": self.max_health,
                "magic_resist": self.magic_resist,
                "crit_chance": self.crit_chance,
                "crit_damage": self.crit_damage,
                "damage": self.damage,
                "element": self.element,
                "regen": self.regen,
                "speed": self.speed,
                "precision": self.precision,
                "evasion": self.evasion,
                "resist": self.resist,
                "type": "Armor",
            }
        )
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Armor":
        return cls(
            name=data["name"],
            description=data["description"],
            value=data["value"],
            # Las armaduras guardadas antes de los huecos no tenían "slot": las tratamos como de peto
            slot=data.get("slot", "peto"),
            defense=data.get("defense", 0),
            max_health=data.get("max_health", 0),
            magic_resist=data.get("magic_resist", 0),
            crit_chance=data.get("crit_chance", 0.0),
            crit_damage=data.get("crit_damage", 0.0),
            damage=data.get("damage", 0),
            element=data.get("element"),
            regen=data.get("regen", 0),
            speed=data.get("speed", 0),
            precision=data.get("precision", 0),
            evasion=data.get("evasion", 0),
            resist=data.get("resist"),
        )
