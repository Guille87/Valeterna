import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats, resolve_hit
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class CustodioDeVidrieras(Enemy):
    DESCRIPTION = (
        "«No mires arriba, a las vidrieras. Aún miran de vuelta.» Esto es lo que hacen cuando de verdad miran."
    )
    SIGNATURE = "Mirada de cristal: puede confundirte además de golpearte con luz astillada."
    ELEMENTS_DEALT = frozenset({"sagrado"})
    INFLICTS = frozenset({"confusion"})
    ENCOUNTER_KIND = "elite"
    ENCOUNTER_LINE = "Los fragmentos de una vidriera rota flotan y se recomponen en una silueta. Un Custodio de Vidrieras te mira de vuelta."
    TAUNT_LINES = (
        "Ya te miré de vuelta una vez. Sigo mirando.",
        "El cristal no olvida la forma de tu derrota.",
    )

    # Tier 7 de la Ciudadela (segundo élite): nacido de un vitral sagrado
    # profanado, pero sagrado al fin y al cabo.
    WEAKNESSES = frozenset({"sagrado"})

    def __init__(self):
        super().__init__(
            "Custodio de Vidrieras",
            Stats(
                1415,
                1415,
                50,
                66,
                20,
                magic_resist=14,
                speed=13,
                precision=16,
                evasion=7,
                crit_chance=0.10,
                crit_damage=1.7,
                magic_penetration=9,
            ),
            gold_min=670,
            gold_max=800,
        )

    def perform_turn(self, player) -> None:
        # Uno de cada cuatro turnos, de media, confunde en vez de atacar.
        if random.random() < 0.25:
            self._glass_gaze(player)
        else:
            self._shattered_light(player)

    def _glass_gaze(self, player) -> None:
        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(
                f"{console.colorize(self.name, console.Fore.MAGENTA)} te mira de vuelta, pero "
                f"{console.colorize(player.name, console.Fore.GREEN)} aparta la vista a tiempo."
            )
            return

        player.apply_status("confusion", duration=3, power=5)
        print(
            f"{console.colorize(self.name, console.Fore.MAGENTA)} te sostiene la mirada de cristal. "
            f"{console.colorize('¡Confundido!', console.Fore.MAGENTA)}"
        )

    def _shattered_light(self, player) -> None:
        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(
                f"{console.colorize(self.name, console.Fore.MAGENTA)} lanza luz astillada, pero "
                f"{console.colorize(player.name, console.Fore.GREEN)} la esquiva."
            )
            return

        is_crit = random.random() < self.stats.crit_chance
        damage = self.get_max_attack_damage() if is_crit else self.get_attack_damage()
        if is_crit:
            damage = int(damage * self.stats.crit_damage)

        final_damage = player.take_damage(
            damage, is_magical=True, magic_penetration=self.stats.magic_penetration, element="sagrado"
        )
        print(
            f"{console.colorize(self.name, console.Fore.MAGENTA)} lanza luz astillada y hace "
            f"{console.colorize(str(final_damage), console.Fore.MAGENTA)} de daño."
            f"{console.crit_suffix(is_crit)}"
        )

    def drop_item(self) -> list:
        items = []
        if random.random() <= 0.5:
            items.append(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20))
        if random.random() <= 0.3:
            items.append(
                Material(
                    "Fragmento de Vidriera",
                    "El color cambia según el ángulo, y a veces según quien lo sostenga.",
                    43,
                    rarity="Raro",
                )
            )
        if random.random() <= 0.1:
            items.append(
                Weapon("Filo de Cristal Sagrado", "Cada golpe suena como una campana rota.", 52, 35, element="sagrado")
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Anillo de Vidriera",
                    "Un cristal de color engarzado, todavía caliente al sol.",
                    68,
                    slot="anillo",
                    crit_damage=0.15,
                )
            )
        return items
