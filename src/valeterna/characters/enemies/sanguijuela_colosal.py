import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats, resolve_hit
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console

# Vida robada (mismo patrón que el Oso Espectral): se cura con una parte del
# daño que inflige en cada mordisco.
_LIFE_DRAIN_RATIO = 0.3


class SanguijuelaColosal(Enemy):
    DESCRIPTION = "Se desliza bajo la superficie sin apenas ondas. Cuando emerge, ya te ha encontrado."
    SIGNATURE = "Mordisco sanguijuela: se cura con parte del daño que inflige."
    ELEMENTS_DEALT = frozenset()
    INFLICTS = frozenset()
    ENCOUNTER_LINE = "El agua se riza sin viento. Una Sanguijuela Colosal rompe la superficie junto a ti."

    # Tier 1 de la Ciénaga: nacida y criada en el agua estancada, el veneno no
    # le hace nada; el fuego, en cambio, la seca de dentro afuera.
    WEAKNESSES = frozenset({"fuego"})
    IMMUNE_ELEMENTS = frozenset({"veneno"})
    IMMUNE_STATUSES = frozenset({"veneno"})

    def __init__(self):
        super().__init__(
            "Sanguijuela Colosal",
            Stats(
                460,
                460,
                15,
                21,
                10,
                magic_resist=2,
                speed=14,
                precision=9,
                evasion=6,
                crit_chance=0.05,
                crit_damage=1.5,
                armor_penetration=3,
            ),
            gold_min=150,
            gold_max=190,
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
            f"{console.colorize(self.name, console.Fore.RED)} se adhiere y hace "
            f"{console.colorize(str(final_damage), console.Fore.RED)} de daño."
            f"{console.crit_suffix(is_crit)}"
        )

        healed = self.heal(round(final_damage * _LIFE_DRAIN_RATIO))
        if healed > 0:
            print(
                f"{console.colorize(self.name, console.Fore.MAGENTA)} se hincha de sangre. "
                f"{console.colorize(f'+{healed} HP', console.Fore.GREEN)}."
            )

    def drop_item(self) -> list:
        items = []
        if random.random() <= 0.5:
            items.append(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20))
        if random.random() <= 0.3:
            items.append(
                Material("Piel de Sanguijuela", "Elástica y viscosa; resbala entre los dedos.", 8, rarity="Común")
            )
        if random.random() <= 0.1:
            items.append(Weapon("Colmillo de Sanguijuela", "Hueco por dentro; sigue succionando aire.", 20, 12))
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Guanteletes de Sanguijuela",
                    "La piel curtida conserva algo de la adherencia del animal.",
                    28,
                    slot="guantes",
                    crit_damage=0.06,
                )
            )
        return items
