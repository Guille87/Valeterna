import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats, resolve_hit
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class MurcielagoDeTormenta(Enemy):
    DESCRIPTION = "Anida en las grietas más altas del cañón, donde el aire siempre huele a tormenta próxima."
    SIGNATURE = "Revoloteo: a veces ataca dos veces seguidas antes de que puedas reaccionar."
    ELEMENTS_DEALT = frozenset()
    INFLICTS = frozenset()
    ENCOUNTER_LINE = (
        "Un chillido agudo rebota entre las paredes del cañón. Un Murciélago de Tormenta se lanza en picado."
    )

    def __init__(self):
        super().__init__(
            "Murciélago de Tormenta",
            Stats(
                640,
                640,
                22,
                30,
                10,
                magic_resist=1,
                speed=18,
                precision=13,
                evasion=11,
                crit_chance=0.08,
                crit_damage=1.6,
                armor_penetration=2,
            ),
            gold_min=240,
            gold_max=290,
        )

    def perform_turn(self, player) -> None:
        """Ataque normal; a veces vuelve a lanzarse antes de que el jugador pueda reaccionar."""
        self._swoop(player, extra=False)

        if self.is_alive() and player.is_alive() and random.random() < 0.3:
            print(console.colorize("¡Vuelve a lanzarse en picado de inmediato!", console.Fore.GREEN))
            self._swoop(player, extra=True)

    def _swoop(self, player, extra: bool) -> None:
        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(
                f"{console.colorize(self.name, console.Fore.RED)} se lanza, pero "
                f"{console.colorize(player.name, console.Fore.GREEN)} logra esquivarlo."
            )
            return

        is_crit = not extra and random.random() < self.stats.crit_chance
        damage = self.get_max_attack_damage() if is_crit else self.get_attack_damage()
        if extra:
            damage = max(1, damage // 2)
        if is_crit:
            damage = int(damage * self.stats.crit_damage)

        final_damage = player.take_damage(damage, armor_penetration=self.stats.armor_penetration)
        print(
            f"{console.colorize(self.name, console.Fore.RED)} araña y hace "
            f"{console.colorize(str(final_damage), console.Fore.RED)} de daño."
            f"{console.crit_suffix(is_crit)}"
        )

    def drop_item(self) -> list:
        items = []
        if random.random() <= 0.5:
            items.append(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20))
        if random.random() <= 0.3:
            items.append(
                Material(
                    "Ala de Tormenta", "Fina como el papel, pero sigue crepitando al tacto.", 19, rarity="Poco común"
                )
            )
        if random.random() <= 0.1:
            items.append(
                Weapon("Garra de Murciélago", "Curvada y ligera; apenas se nota hasta que ya ha cortado.", 32, 22)
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Perneras de Ala",
                    "Cosidas con membrana de murciélago; casi no pesan.",
                    38,
                    slot="perneras",
                    evasion=5,
                )
            )
        return items
