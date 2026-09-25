import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats, resolve_hit
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class SacerdoteAhogado(Enemy):
    DESCRIPTION = "Ofició en el templo antes de que se hundiera con él. Sigue oficiando, aunque ya no haya fieles."
    SIGNATURE = "Cántico ahogado: puede confundirte además de golpearte con magia oscura."
    ELEMENTS_DEALT = frozenset({"oscuridad"})
    INFLICTS = frozenset({"confusion"})
    ENCOUNTER_KIND = "elite"
    ENCOUNTER_LINE = "Un cántico gorgoteante sube desde el agua turbia. Un Sacerdote Ahogado emerge, aún rezando."
    TAUNT_LINES = (
        "El cántico no termina solo porque tú caigas.",
        "Ya rezaba por tu derrota antes de que llegaras.",
    )

    # Tier 7 de la Ciénaga (segundo élite): sirve a lo mismo que el Chamán del
    # Cieno, con las mismas afinidades.
    WEAKNESSES = frozenset({"sagrado"})
    RESISTANCES = frozenset({"oscuridad"})

    def __init__(self):
        super().__init__(
            "Sacerdote Ahogado",
            Stats(
                545,
                545,
                22,
                30,
                12,
                magic_resist=8,
                speed=12,
                precision=13,
                evasion=5,
                crit_chance=0.08,
                crit_damage=1.6,
                magic_penetration=5,
            ),
            gold_min=200,
            gold_max=240,
        )

    def perform_turn(self, player) -> None:
        # Uno de cada cuatro turnos, de media, confunde en vez de atacar.
        if random.random() < 0.25:
            self._cast_confusion(player)
        else:
            self._dark_chant(player)

    def _cast_confusion(self, player) -> None:
        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(
                f"{console.colorize(self.name, console.Fore.MAGENTA)} entona un cántico, pero "
                f"{console.colorize(player.name, console.Fore.GREEN)} no se deja alcanzar por él."
            )
            return

        player.apply_status("confusion", duration=3, power=5)
        print(
            f"{console.colorize(self.name, console.Fore.MAGENTA)} entona un cántico gorgoteante que se te mete "
            f"en la cabeza. {console.colorize('¡Confundido!', console.Fore.MAGENTA)}"
        )

    def _dark_chant(self, player) -> None:
        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(
                f"{console.colorize(self.name, console.Fore.MAGENTA)} lanza un rezo corrupto, pero "
                f"{console.colorize(player.name, console.Fore.GREEN)} lo esquiva."
            )
            return

        is_crit = random.random() < self.stats.crit_chance
        damage = self.get_max_attack_damage() if is_crit else self.get_attack_damage()
        if is_crit:
            damage = int(damage * self.stats.crit_damage)

        final_damage = player.take_damage(
            damage, is_magical=True, magic_penetration=self.stats.magic_penetration, element="oscuridad"
        )
        print(
            f"{console.colorize(self.name, console.Fore.MAGENTA)} lanza un rezo corrupto y hace "
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
                    "Reliquia Ahogada",
                    "Un colgante de templo, ennegrecido por años bajo el agua.",
                    12,
                    rarity="Poco común",
                )
            )
        if random.random() <= 0.1:
            items.append(
                Weapon(
                    "Báculo Ahogado",
                    "Todavía gotea agua estancada que no debería seguir ahí.",
                    25,
                    17,
                    element="oscuridad",
                )
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Hombreras del Templo",
                    "Grabadas con el mismo relieve que cubre las paredes hundidas.",
                    30,
                    slot="hombreras",
                    precision=6,
                    magic_resist=2,
                )
            )
        return items
