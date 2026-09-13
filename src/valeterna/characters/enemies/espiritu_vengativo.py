import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats, resolve_hit
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class EspirituVengativo(Enemy):
    def __init__(self):
        # Incorpóreo: poca armadura propia, pero sus proyectiles espectrales
        # ignoran buena parte de la del objetivo (armor_penetration alto).
        super().__init__(
            "Espíritu Vengativo",
            Stats(
                210,
                210,
                18,
                26,
                3,
                magic_resist=2,
                speed=17,
                precision=10,
                evasion=9,
                crit_chance=0.08,
                crit_damage=1.7,
                armor_penetration=8,
            ),
            gold_min=30,
            gold_max=40,
        )

    def perform_turn(self, player) -> None:
        # Un turno de cada cuatro, de media, maldice en vez de atacar.
        if random.random() < 0.25:
            self._cast_curse(player)
        else:
            super().perform_turn(player)

    def _cast_curse(self, player) -> None:
        """Maldición: reduce la armadura efectiva del jugador durante unos turnos."""
        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(
                f"{console.colorize(self.name, console.Fore.MAGENTA)} intenta maldecir a "
                f"{console.colorize(player.name, console.Fore.GREEN)}, pero falla."
            )
            return

        player.apply_status("maldicion", duration=3, power=4)
        print(
            f"{console.colorize(self.name, console.Fore.MAGENTA)} pronuncia palabras de ultratumba. "
            f"{console.colorize('¡Maldito! -4 de armadura durante 3 turnos.', console.Fore.MAGENTA)}"
        )

    def drop_item(self) -> list:
        items = []
        if random.random() <= 0.5:
            items.append(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20))
        if random.random() <= 0.3:
            items.append(
                Material(
                    "Esencia Espectral", "Un jirón de energía fantasmal que se resiste a disiparse.", 10, rarity="Raro"
                )
            )
        if random.random() <= 0.1:
            items.append(
                Weapon("Daga Espectral", "Fría al tacto; parece atravesar la carne sin apenas resistencia.", 18, 14)
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Brazales Espectrales",
                    "Envuelven el brazo en una neblina fría que no se puede tocar del todo.",
                    22,
                    slot="brazales",
                    crit_chance=0.04,
                    magic_resist=4,
                )
            )
        return items
