import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats, resolve_hit
from valeterna.items.equipment import Armor
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class OgroDelYermo(Enemy):
    DESCRIPTION = "El terror de las caravanas: lo que no aplasta de un golpe, lo dispersa del susto."
    SIGNATURE = "Golpe aplastante: un mazazo más fuerte de lo normal que puede dejarte aturdido."
    ELEMENTS_DEALT = frozenset()
    INFLICTS = frozenset({"aturdido"})
    ENCOUNTER_KIND = "elite"
    ENCOUNTER_LINE = "El suelo tiembla: un Ogro del Yermo se acerca, y no parece de buen humor."
    TAUNT_LINES = (
        "La última vez ya te dejé aturdido. Hoy no seré tan blando.",
        "Sigues en pie. Eso tiene fácil arreglo.",
    )

    # Su corpachón no distingue una descarga de otra: no se le puede aturdir.
    WEAKNESSES = frozenset({"fuego"})
    IMMUNE_STATUSES = frozenset({"paralizado"})

    def __init__(self):
        # Segundo élite de Los Yermos: bruiser puro, mucha vida y ataque, poca
        # evasión (no la necesita).
        super().__init__(
            "Ogro del Yermo",
            Stats(
                241,
                241,
                56,
                80,
                5,
                speed=9,
                precision=8,
                evasion=1,
                crit_chance=0.05,
                crit_damage=1.5,
                armor_penetration=4,
            ),
            gold_min=30,
            gold_max=38,
        )

    def perform_turn(self, player) -> None:
        # Un turno de cada cinco, de media, mazazo en vez de golpe normal.
        if random.random() < 0.2:
            self._crushing_blow(player)
        else:
            super().perform_turn(player)

    def _crushing_blow(self, player) -> None:
        print(console.colorize(f"{self.name} alza su maza por encima de la cabeza...", console.Fore.RED))

        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(f"El mazazo cae, pero {console.colorize(player.name, console.Fore.GREEN)} logra apartarse a tiempo.")
            return

        damage = int(self.get_attack_damage() * 1.6)
        final_damage = player.take_damage(damage, armor_penetration=self.stats.armor_penetration)
        print(f"¡Golpe aplastante! {console.colorize(str(final_damage), console.Fore.RED)} de daño.")

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
                    "Piel de Ogro",
                    "Gruesa y correosa; cuesta encontrar un cuchillo que la atraviese.",
                    5,
                    rarity="Común",
                )
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Yelmo de Ogro",
                    "Tallado en un solo hueso, todavía con las marcas de los golpes recibidos.",
                    20,
                    slot="casco",
                    max_health=22,
                )
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Cinturón Trenzado",
                    "Trenzado con tendones; aguanta más de lo que parece.",
                    17,
                    slot="cinturon",
                    defense=3,
                )
            )
        return items
