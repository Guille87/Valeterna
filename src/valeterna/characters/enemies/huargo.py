import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats, resolve_hit
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class Huargo(Enemy):
    DESCRIPTION = "Lobo enorme de ojos ambarinos que caza en manada por los Yermos."
    SIGNATURE = "Mordisco de manada: a veces otro lobo se suma al ataque con un mordisco extra."
    ELEMENTS_DEALT = frozenset()
    INFLICTS = frozenset()
    ENCOUNTER_LINE = "Un Huargo te corta el paso, gruñendo bajo."

    def __init__(self):
        # Lobo salvaje: rápido y evasivo, pero frágil (poca vida y armadura).
        super().__init__(
            "Huargo",
            Stats(66, 66, 19, 28, 1, speed=13, precision=6, evasion=4, crit_chance=0.05, crit_damage=1.5),
            gold_min=6,
            gold_max=9,
        )

    def perform_turn(self, player) -> None:
        """Ataque normal; a veces caza en manada y otro lobo se suma con un mordisco extra."""
        super().perform_turn(player)

        if self.is_alive() and player.is_alive() and random.random() < 0.2:
            print(console.colorize("¡El resto de la manada aprovecha el hueco!", console.Fore.RED))
            self._pack_bite(player)

    def _pack_bite(self, player) -> None:
        """Segundo mordisco de un compañero de manada: más débil que el ataque principal."""
        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(f"{console.colorize(self.name, console.Fore.RED)} falla el mordisco de manada.")
            return

        damage = max(1, self.get_attack_damage() // 2)
        final_damage = player.take_damage(damage, armor_penetration=self.stats.armor_penetration)
        print(f"El mordisco de manada hace {console.colorize(str(final_damage), console.Fore.RED)} de daño extra.")

    def drop_item(self) -> list:
        items = []
        if random.random() <= 0.7:
            items.append(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20))
        if random.random() <= 0.3:
            items.append(
                Material("Colmillo de Huargo", "Un colmillo curvo, todavía caliente de la caza.", 5, rarity="Común")
            )
        if random.random() <= 0.1:
            items.append(
                Weapon("Garras de Huargo", "Un par de garras montadas en guantelete, aún manchadas de sangre.", 10, 7)
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Botas de Huargo",
                    "Cosidas con las patas del propio lobo; todavía conservan su agilidad.",
                    15,
                    slot="botas",
                    speed=2,
                )
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Cinturón de Manada",
                    "Trenzado con tiras de cuero de varios lobos; imita su ritmo de carrera.",
                    12,
                    slot="cinturon",
                    defense=2,
                    speed=2,
                )
            )
        return items
