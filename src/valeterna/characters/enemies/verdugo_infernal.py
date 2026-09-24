import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats, resolve_hit
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console

# Vida robada (mismo patrón que la Sanguijuela Colosal, el Oso Espectral y
# el Carroñero de Cripta): se cura con una parte del daño que inflige.
_LIFE_DRAIN_RATIO = 0.3


class VerdugoInfernal(Enemy):
    DESCRIPTION = "Sirve a lo que gobierna la Ciudadela, no al Demonio que arde en la Plaza. Cobra sus deudas en carne."
    SIGNATURE = "Cobro de sangre: se cura con parte del daño que inflige."
    ELEMENTS_DEALT = frozenset()
    INFLICTS = frozenset()
    ENCOUNTER_LINE = "Cadenas al rojo arrastran algo por los escombros. Un Verdugo Infernal viene a cobrar."

    # Tier 8 de la Ciudadela: cobra en carne, no en fe, así que lo sagrado
    # sigue siendo lo único que lo detiene.
    WEAKNESSES = frozenset({"sagrado"})

    def __init__(self):
        super().__init__(
            "Verdugo Infernal",
            Stats(
                1555,
                1555,
                46,
                61,
                18,
                magic_resist=10,
                speed=14,
                precision=14,
                evasion=6,
                crit_chance=0.08,
                crit_damage=1.6,
                armor_penetration=8,
            ),
            gold_min=700,
            gold_max=835,
        )

    def perform_turn(self, player) -> None:
        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(
                f"{console.colorize(self.name, console.Fore.RED)} tira de sus cadenas, pero "
                f"{console.colorize(player.name, console.Fore.GREEN)} logra esquivarlas."
            )
            return

        is_crit = random.random() < self.stats.crit_chance
        damage = self.get_max_attack_damage() if is_crit else self.get_attack_damage()
        if is_crit:
            damage = int(damage * self.stats.crit_damage)

        final_damage = player.take_damage(damage, armor_penetration=self.stats.armor_penetration)
        print(
            f"{console.colorize(self.name, console.Fore.RED)} golpea con sus cadenas y hace "
            f"{console.colorize(str(final_damage), console.Fore.RED)} de daño."
            f"{console.crit_suffix(is_crit)}"
        )

        healed = self.heal(round(final_damage * _LIFE_DRAIN_RATIO))
        if healed > 0:
            print(
                f"{console.colorize(self.name, console.Fore.MAGENTA)} cobra su deuda de sangre. "
                f"{console.colorize(f'+{healed} HP', console.Fore.GREEN)}."
            )

    def drop_item(self) -> list:
        items = []
        if random.random() <= 0.5:
            items.append(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20))
        if random.random() <= 0.3:
            items.append(
                Material(
                    "Eslabón al Rojo", "Sigue caliente mucho después de arrancarlo de la cadena.", 44, rarity="Raro"
                )
            )
        if random.random() <= 0.1:
            items.append(Weapon("Cadena de Cobro", "Cada eslabón está marcado, como si llevara la cuenta.", 53, 36))
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Guanteletes de Verdugo",
                    "El cuero está curtido en algo que no es solo sudor.",
                    74,
                    slot="guantes",
                    crit_damage=0.12,
                )
            )
        return items
