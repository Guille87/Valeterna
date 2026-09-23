import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats, resolve_hit
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class CabraMontesCorrupta(Enemy):
    DESCRIPTION = "Saltaba entre los riscos antes de que la corrupción de la Brecha le torciera los cuernos."
    SIGNATURE = "Topetazo: un golpe más fuerte de lo normal que puede dejarte aturdido."
    ELEMENTS_DEALT = frozenset()
    INFLICTS = frozenset({"aturdido"})
    ENCOUNTER_LINE = "Un golpe de pezuñas resuena en la roca. Una Cabra Montés Corrupta carga desde el risco."

    def __init__(self):
        super().__init__(
            "Cabra Montés Corrupta",
            Stats(
                770,
                770,
                28,
                38,
                14,
                magic_resist=2,
                speed=16,
                precision=12,
                evasion=7,
                crit_chance=0.08,
                crit_damage=1.6,
                armor_penetration=4,
            ),
            gold_min=290,
            gold_max=345,
        )

    def perform_turn(self, player) -> None:
        # Un turno de cada cinco, de media, topetazo en vez de golpe normal.
        if random.random() < 0.2:
            self._headbutt(player)
        else:
            super().perform_turn(player)

    def _headbutt(self, player) -> None:
        print(console.colorize(f"{self.name} baja los cuernos y toma impulso...", console.Fore.RED))

        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(
                f"El topetazo llega, pero {console.colorize(player.name, console.Fore.GREEN)} logra apartarse a tiempo."
            )
            return

        damage = int(self.get_attack_damage() * 1.6)
        final_damage = player.take_damage(damage, armor_penetration=self.stats.armor_penetration)
        print(f"¡Topetazo! {console.colorize(str(final_damage), console.Fore.RED)} de daño.")

        if random.random() < 0.4:
            player.apply_status("aturdido", 1)
            console.warning("¡El golpe te ha dejado aturdido!")

    def drop_item(self) -> list:
        items = []
        if random.random() <= 0.55:
            items.append(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20))
        if random.random() <= 0.3:
            items.append(
                Material(
                    "Cuerno Retorcido", "Se curva en un ángulo que ningún cuerno sano tomaría.", 22, rarity="Poco común"
                )
            )
        if random.random() <= 0.08:
            items.append(
                Weapon("Cuerno Afilado", "Pulido en la punta, como si algo lo hubiera afilado a propósito.", 34, 23)
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Botas de Cabra",
                    "El agarre es tan bueno que casi no se siente el borde del abismo.",
                    40,
                    slot="botas",
                    speed=4,
                )
            )
        return items
