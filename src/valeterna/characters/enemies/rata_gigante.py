import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats, resolve_hit
from valeterna.items.equipment import Armor
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class RataGigante(Enemy):
    DESCRIPTION = "El primer peligro real de los Yermos: rápida, sucia y siempre en manada, aunque ataque sola."
    SIGNATURE = "Mordisco rápido: puede envenenar con cada ataque."
    ELEMENTS_DEALT = frozenset()
    INFLICTS = frozenset({"veneno"})
    ENCOUNTER_LINE = "Una Rata Gigante te enseña los dientes desde la maleza."

    # Debilidad tal como manda el GDD §4.6 (tier 1 de Los Yermos): el fuego
    # acaba con el nido antes de que pueda huir.
    WEAKNESSES = frozenset({"fuego"})

    def __init__(self):
        # Rápida y frágil, pero por delante del Goblin en poder real (feedback
        # del usuario tras jugar: se desbloquea justo después de él, así que
        # debía notarse más difícil, no menos — ver TODO.md).
        super().__init__(
            "Rata Gigante",
            Stats(36, 36, 8, 14, 1, speed=15, precision=6, evasion=4, crit_chance=0.05, crit_damage=1.5),
            gold_min=5,
            gold_max=8,
        )

    def perform_turn(self, player) -> None:
        """Ataque normal; a veces el mordisco deja una infección que envenena."""
        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(
                f"{console.colorize(self.name, console.Fore.RED)} ataca, pero "
                f"{console.colorize(player.name, console.Fore.GREEN)} esquiva el mordisco."
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

        if random.random() < 0.25:
            player.apply_status("veneno", 2)
            print(console.colorize("¡La mordedura estaba infectada!", console.Fore.GREEN))
            reaction_msg = player.pop_status_reaction_message()
            if reaction_msg:
                print(reaction_msg)

    def drop_item(self) -> list:
        items = []
        if random.random() <= 0.7:
            items.append(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20))
        if random.random() <= 0.25:
            items.append(
                Material("Cola de Rata", "Correosa y resistente, casi imposible de cortar.", 2, rarity="Común")
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Botas de Piel de Rata",
                    "Ligeras y silenciosas, cosidas para correr entre la maleza.",
                    10,
                    slot="botas",
                    speed=1,
                )
            )
        return items
