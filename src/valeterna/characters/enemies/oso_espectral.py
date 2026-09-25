import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats, resolve_hit
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console

# Vida robada (GDD §4.5): se cura con una parte del daño que inflige, en vez
# de curarse bajo un umbral de vida como el Druida o el Mago.
_LIFE_DRAIN_RATIO = 0.3


class OsoEspectral(Enemy):
    DESCRIPTION = "El espíritu de la última osa que cazó en este bosque, antes de que dejara de haber presas de verdad."
    SIGNATURE = "Zarpazo vampírico: se cura con parte del daño que inflige."
    ELEMENTS_DEALT = frozenset()
    INFLICTS = frozenset()
    ENCOUNTER_LINE = (
        "Una forma pálida y enorme se alza entre los árboles. El Oso Espectral no respira, pero ruge igual."
    )

    # Tier 6 del Bosque: lo sagrado inquieta a un espíritu que no debería seguir
    # aquí; sin sangre ni veneno que corromper, el veneno no le afecta.
    WEAKNESSES = frozenset({"sagrado"})
    IMMUNE_ELEMENTS = frozenset({"veneno"})
    IMMUNE_STATUSES = frozenset({"veneno"})

    def __init__(self):
        super().__init__(
            "Oso Espectral",
            Stats(
                356,
                356,
                25,
                33,
                6,
                magic_resist=3,
                speed=11,
                precision=9,
                evasion=2,
                crit_chance=0.05,
                crit_damage=1.5,
                armor_penetration=4,
            ),
            gold_min=95,
            gold_max=120,
        )

    def perform_turn(self, player) -> None:
        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(
                f"{console.colorize(self.name, console.Fore.RED)} zarpea el aire; "
                f"{console.colorize(player.name, console.Fore.GREEN)} logra apartarse."
            )
            return

        is_crit = random.random() < self.stats.crit_chance
        damage = self.get_max_attack_damage() if is_crit else self.get_attack_damage()
        if is_crit:
            damage = int(damage * self.stats.crit_damage)

        final_damage = player.take_damage(damage, armor_penetration=self.stats.armor_penetration)
        print(
            f"{console.colorize(self.name, console.Fore.RED)} zarpea y hace "
            f"{console.colorize(str(final_damage), console.Fore.RED)} de daño."
            f"{console.crit_suffix(is_crit)}"
        )

        healed = self.heal(round(final_damage * _LIFE_DRAIN_RATIO))
        if healed > 0:
            print(
                f"{console.colorize(self.name, console.Fore.MAGENTA)} absorbe parte de la herida. "
                f"{console.colorize(f'+{healed} HP', console.Fore.GREEN)}."
            )

    def drop_item(self) -> list:
        items = []
        if random.random() <= 0.5:
            items.append(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20))
        if random.random() <= 0.3:
            items.append(
                Material(
                    "Pelaje Espectral", "Frío al tacto incluso cuando no hay nada que tocar.", 9, rarity="Poco común"
                )
            )
        if random.random() <= 0.1:
            items.append(Weapon("Garra Espectral", "Se sostiene en la mano sin llegar a pesar del todo.", 26, 17))
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Cráneo de Oso Espectral",
                    "Hueco por dentro; el frío que desprende no baja nunca.",
                    30,
                    slot="casco",
                    max_health=20,
                )
            )
        return items
