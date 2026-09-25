import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats, resolve_hit
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console

# Robo de oro (v0.14.0-c, feedback del usuario): nada de "roba todo el rato" ni
# de dejar al jugador sin nada. `_STEAL_CHANCE` hace que sea una acción
# minoritaria (como la maldición del Espíritu Vengativo o la carga de la
# Gárgola: alterna con el ataque normal, no lo sustituye), y el importe es un
# rango fijo y pequeño, siempre acotado a lo que el jugador lleve encima.
_STEAL_CHANCE = 0.25
_STEAL_MIN, _STEAL_MAX = 3, 8


class Salteador(Enemy):
    DESCRIPTION = "Más rápido que el Bandido y con menos escrúpulos: prefiere tu bolsa a tu vida."
    SIGNATURE = "Doble golpe y manos largas: a veces golpea dos veces seguidas, otras veces prefiere robarte el oro."
    ELEMENTS_DEALT = frozenset()
    INFLICTS = frozenset()
    ENCOUNTER_LINE = "Un Salteador te mide de arriba abajo, calculando cuánto llevas encima."

    def __init__(self):
        # Skirmisher rápido y con buen ataque, pero armadura discreta.
        super().__init__(
            "Salteador",
            Stats(
                106,
                106,
                16,
                24,
                3,
                speed=12,
                precision=9,
                evasion=4,
                crit_chance=0.06,
                crit_damage=1.5,
                armor_penetration=2,
            ),
            gold_min=20,
            gold_max=26,
        )

    def perform_turn(self, player) -> None:
        """Un turno de cada cuatro, de media, roba en vez de atacar. El resto de
        turnos ataca con normalidad, y a veces remata con un segundo golpe más
        débil (mismo patrón que el mordisco de manada del Huargo)."""
        if random.random() < _STEAL_CHANCE:
            self._steal(player)
            return

        super().perform_turn(player)

        if self.is_alive() and player.is_alive() and random.random() < 0.3:
            print(console.colorize("¡El Salteador es más rápido de lo que parece!", console.Fore.RED))
            self._second_strike(player)

    def _second_strike(self, player) -> None:
        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(f"{console.colorize(self.name, console.Fore.RED)} falla el segundo golpe.")
            return

        damage = max(1, self.get_attack_damage() // 2)
        final_damage = player.take_damage(damage, armor_penetration=self.stats.armor_penetration)
        print(f"El segundo golpe hace {console.colorize(str(final_damage), console.Fore.RED)} de daño extra.")

    def _steal(self, player) -> None:
        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(
                f"{console.colorize(self.name, console.Fore.RED)} intenta rebuscar en tu bolsa, pero "
                f"{console.colorize(player.name, console.Fore.GREEN)} lo aparta a tiempo."
            )
            return

        amount = min(player.inventory.gold, random.randint(_STEAL_MIN, _STEAL_MAX))
        if amount <= 0:
            print(f"{console.colorize(self.name, console.Fore.RED)} rebusca en tu bolsa, pero no lleva nada.")
            return

        player.inventory.gold -= amount
        print(
            f"{console.colorize(self.name, console.Fore.RED)} te roba "
            f"{console.colorize(f'{amount} de oro', console.Fore.YELLOW)} y desaparece entre la maleza."
        )

    def drop_item(self) -> list:
        items = []
        if random.random() <= 0.55:
            items.append(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20))
        if random.random() <= 0.3:
            items.append(Material("Bolsa Remendada", "Cosida con retales de otras tantas víctimas.", 4, rarity="Común"))
        if random.random() <= 0.1:
            items.append(Weapon("Dagas Gemelas", "Un par de dagas idénticas, afiladas por los dos lados.", 13, 10))
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Guantes de Saltador",
                    "Sin apenas grosor; hechos para no perder ni un segundo al agarrar.",
                    17,
                    slot="guantes",
                    crit_damage=0.13,
                )
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Perneras Ligeras",
                    "Cortadas para no hacer ruido al correr entre la maleza.",
                    15,
                    slot="perneras",
                    evasion=3,
                )
            )
        return items
