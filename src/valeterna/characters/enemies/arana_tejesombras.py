import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats, resolve_hit
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class AranaTejesombras(Enemy):
    DESCRIPTION = "Teje entre las ramas más altas del Bosque, donde la luz ya no llega. Baja solo para cazar."
    SIGNATURE = "Mordisco venenoso: su picadura puede envenenarte con cada golpe."
    ELEMENTS_DEALT = frozenset()
    INFLICTS = frozenset({"veneno"})
    ENCOUNTER_LINE = "Algo se mueve entre las ramas altas. Una Araña Tejesombras baja hacia ti, hilo a hilo."

    # Tier 4 del Bosque (GDD §4.1: tiers 1-4/6/8 estándar): el fuego quema la
    # telaraña antes de que pueda usarla.
    WEAKNESSES = frozenset({"fuego"})

    def __init__(self):
        super().__init__(
            "Araña Tejesombras",
            Stats(
                160,
                160,
                15,
                20,
                3,
                magic_resist=0,
                speed=16,
                precision=11,
                evasion=8,
                crit_chance=0.06,
                crit_damage=1.5,
                armor_penetration=2,
            ),
            gold_min=60,
            gold_max=75,
        )

    def perform_turn(self, player) -> None:
        """Ataque normal; su mordisco puede dejar una infección venenosa."""
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

        if random.random() < 0.3:
            player.apply_status("veneno", 3)
            print(console.colorize("¡El veneno recorre la herida!", console.Fore.GREEN))
            reaction_msg = player.pop_status_reaction_message()
            if reaction_msg:
                print(reaction_msg)

    def drop_item(self) -> list:
        items = []
        if random.random() <= 0.55:
            items.append(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20))
        if random.random() <= 0.3:
            items.append(
                Material(
                    "Seda de Tejesombras", "Un hilo negro, ligero pero casi imposible de romper.", 6, rarity="Común"
                )
            )
        if random.random() <= 0.1:
            items.append(
                Weapon("Colmillo de Tejesombras", "Todavía gotea un veneno espeso y oscuro.", 20, 12, element="veneno")
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Perneras de Tejedora",
                    "Tejidas con la misma seda que la araña usaba para colgarse de las ramas.",
                    24,
                    slot="perneras",
                    evasion=3,
                )
            )
        return items
