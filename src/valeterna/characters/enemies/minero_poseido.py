import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats, resolve_hit
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class MineroPoseido(Enemy):
    DESCRIPTION = "Uno de los catorce que la galería se tragó. Sigue moviéndose, y sigue sujetando su pico."
    SIGNATURE = "Picoazo: los golpes de su pico pueden dejar una herida que sigue sangrando."
    ELEMENTS_DEALT = frozenset()
    INFLICTS = frozenset({"sangrado"})
    ENCOUNTER_LINE = "En la oscuridad de la galería, algo arrastra un pico contra la roca. Un Minero Poseído emerge."

    # Tier 3 del Cañón: no queda nada vivo que salvar, así que lo sagrado es
    # lo único que perturba a lo que quedó de él.
    WEAKNESSES = frozenset({"sagrado"})

    def __init__(self):
        super().__init__(
            "Minero Poseído",
            Stats(
                850,
                850,
                28,
                38,
                17,
                magic_resist=2,
                speed=10,
                precision=9,
                evasion=1,
                crit_chance=0.06,
                crit_damage=1.6,
                armor_penetration=5,
            ),
            gold_min=225,
            gold_max=270,
        )

    def perform_turn(self, player) -> None:
        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(
                f"{console.colorize(self.name, console.Fore.RED)} lanza un picoazo, pero "
                f"{console.colorize(player.name, console.Fore.GREEN)} logra apartarse."
            )
            return

        is_crit = random.random() < self.stats.crit_chance
        damage = self.get_max_attack_damage() if is_crit else self.get_attack_damage()
        if is_crit:
            damage = int(damage * self.stats.crit_damage)

        final_damage = player.take_damage(damage, armor_penetration=self.stats.armor_penetration)
        print(
            f"{console.colorize(self.name, console.Fore.RED)} golpea con el pico y hace "
            f"{console.colorize(str(final_damage), console.Fore.RED)} de daño."
            f"{console.crit_suffix(is_crit)}"
        )

        if random.random() < 0.3:
            player.apply_status("sangrado", 3)
            print(console.colorize("¡El pico deja un corte profundo!", console.Fore.RED))
            reaction_msg = player.pop_status_reaction_message()
            if reaction_msg:
                print(reaction_msg)

    def drop_item(self) -> list:
        items = []
        if random.random() <= 0.5:
            items.append(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20))
        if random.random() <= 0.3:
            items.append(
                Material("Pico Roto", "El mango está astillado, pero la punta sigue firme.", 18, rarity="Poco común")
            )
        if random.random() <= 0.1:
            items.append(
                Weapon("Pico de Minero", "Pesado y desequilibrado, pensado para la roca, no para carne.", 30, 21)
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Casco de Minero",
                    "Abollado por dentro, como si algo hubiera intentado salir por la fuerza.",
                    45,
                    slot="casco",
                    max_health=28,
                )
            )
        return items
