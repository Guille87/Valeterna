import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats, resolve_hit
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console

# Vida robada (mismo patrón que la Sanguijuela Colosal y el Oso Espectral):
# se cura con una parte del daño que inflige en cada mordisco.
_LIFE_DRAIN_RATIO = 0.3


class CarroneroDeCripta(Enemy):
    DESCRIPTION = "Vive de lo que la Cripta no termina de enterrar. Cuanto más come, menos hambre parece tener."
    SIGNATURE = "Mordisco carroñero: se cura con parte del daño que inflige."
    ELEMENTS_DEALT = frozenset()
    INFLICTS = frozenset()
    ENCOUNTER_LINE = "Un olor a tierra removida llega antes que él. Un Carroñero de Cripta sale de entre las losas."

    # Tier 8 de la Torre: lo sagrado inquieta a algo que se alimenta de los
    # muertos; el veneno, en cambio, no le hace gran cosa a algo ya podrido.
    WEAKNESSES = frozenset({"sagrado"})
    RESISTANCES = frozenset({"veneno"})

    def __init__(self):
        super().__init__(
            "Carroñero de Cripta",
            Stats(
                1100,
                1100,
                34,
                46,
                12,
                magic_resist=5,
                speed=15,
                precision=12,
                evasion=7,
                crit_chance=0.06,
                crit_damage=1.6,
                armor_penetration=6,
            ),
            gold_min=460,
            gold_max=550,
        )

    def perform_turn(self, player) -> None:
        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(
                f"{console.colorize(self.name, console.Fore.RED)} se lanza, pero "
                f"{console.colorize(player.name, console.Fore.GREEN)} logra apartarse."
            )
            return

        is_crit = random.random() < self.stats.crit_chance
        damage = self.get_max_attack_damage() if is_crit else self.get_attack_damage()
        if is_crit:
            damage = int(damage * self.stats.crit_damage)

        final_damage = player.take_damage(damage, armor_penetration=self.stats.armor_penetration)
        print(
            f"{console.colorize(self.name, console.Fore.RED)} muerde y hace "
            f"{console.colorize(str(final_damage), console.Fore.RED)} de daño."
            f"{console.crit_suffix(is_crit)}"
        )

        healed = self.heal(round(final_damage * _LIFE_DRAIN_RATIO))
        if healed > 0:
            print(
                f"{console.colorize(self.name, console.Fore.MAGENTA)} devora parte de la herida. "
                f"{console.colorize(f'+{healed} HP', console.Fore.GREEN)}."
            )

    def drop_item(self) -> list:
        items = []
        if random.random() <= 0.5:
            items.append(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20))
        if random.random() <= 0.3:
            items.append(
                Material(
                    "Colmillo Carroñero",
                    "Amarillento y curvo; huele a tierra por mucho que se limpie.",
                    32,
                    rarity="Raro",
                )
            )
        if random.random() <= 0.1:
            items.append(
                Weapon("Garra de Cripta", "Sigue teniendo tierra bajo las uñas por mucho que la afiles.", 42, 28)
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Botas de Carroñero",
                    "No hacen ruido sobre la piedra suelta de la Cripta.",
                    58,
                    slot="botas",
                    speed=5,
                )
            )
        return items
