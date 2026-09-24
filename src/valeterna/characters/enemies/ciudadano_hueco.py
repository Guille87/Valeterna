import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats, resolve_hit
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class CiudadanoHueco(Enemy):
    DESCRIPTION = "Uno de los que acudieron a la catedral cuando se les ordenó. En la Plaza solo quedaron los zapatos."
    SIGNATURE = "Pánico ciego: puede arrancarte el arma de las manos al golpear."
    ELEMENTS_DEALT = frozenset()
    INFLICTS = frozenset({"desarmado"})
    ENCOUNTER_LINE = "Una figura descalza avanza entre los escombros de la Plaza. Un Ciudadano Hueco te alcanza."

    # Tier 3 de la Ciudadela: ya no queda nadie dentro, solo lo sagrado
    # perturba lo que quedó vacío.
    WEAKNESSES = frozenset({"sagrado"})

    def __init__(self):
        super().__init__(
            "Ciudadano Hueco",
            Stats(
                1365,
                1365,
                40,
                54,
                16,
                magic_resist=6,
                speed=13,
                precision=11,
                evasion=5,
                crit_chance=0.07,
                crit_damage=1.6,
                armor_penetration=6,
            ),
            gold_min=550,
            gold_max=655,
        )

    def perform_turn(self, player) -> None:
        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(
                f"{console.colorize(self.name, console.Fore.RED)} se abalanza, pero "
                f"{console.colorize(player.name, console.Fore.GREEN)} logra apartarse."
            )
            return

        is_crit = random.random() < self.stats.crit_chance
        damage = self.get_max_attack_damage() if is_crit else self.get_attack_damage()
        if is_crit:
            damage = int(damage * self.stats.crit_damage)

        final_damage = player.take_damage(damage, armor_penetration=self.stats.armor_penetration)
        print(
            f"{console.colorize(self.name, console.Fore.RED)} se aferra y hace "
            f"{console.colorize(str(final_damage), console.Fore.RED)} de daño."
            f"{console.crit_suffix(is_crit)}"
        )

        if random.random() < 0.25:
            player.apply_status("desarmado", 2)
            print(console.colorize("¡Te ha arrancado el arma de las manos!", console.Fore.YELLOW))

    def drop_item(self) -> list:
        items = []
        if random.random() <= 0.5:
            items.append(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20))
        if random.random() <= 0.3:
            items.append(
                Material(
                    "Zapato Abandonado",
                    "No es de tu talla, ni de la de nadie que vaya a volver a por él.",
                    38,
                    rarity="Poco común",
                )
            )
        if random.random() <= 0.1:
            items.append(
                Weapon("Puño Hueco", "Frío y ligero, como si dentro no quedara nada que le diera peso.", 47, 32)
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Perneras de Ciudadano",
                    "Ropa de calle rígida, como si el miedo la hubiera almidonado.",
                    64,
                    slot="perneras",
                    evasion=6,
                )
            )
        return items
