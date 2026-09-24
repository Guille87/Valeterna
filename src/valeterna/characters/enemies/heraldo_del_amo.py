import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class HeraldoDelAmo(Enemy):
    DESCRIPTION = "«No he visto su rostro. Los ángeles caídos le sirven. Los demonios solo lo temen.» Esto es lo que envía por delante."
    SIGNATURE = "Proclama: de vez en cuando pronuncia una sentencia imposible de esquivar."
    ELEMENTS_DEALT = frozenset()
    INFLICTS = frozenset()
    ENCOUNTER_LINE = "Una voz que no debería tener boca anuncia algo en una lengua que duele escuchar. Un Heraldo del Amo se presenta."

    # Tier 9 de la Ciudadela (tercer élite): habla en nombre de lo que
    # gobierna, no de un cuerpo; sin nervios, no hay parálisis que valga.
    WEAKNESSES = frozenset({"sagrado"})
    IMMUNE_STATUSES = frozenset({"paralizado"})

    def __init__(self):
        super().__init__(
            "Heraldo del Amo",
            Stats(
                2090,
                2090,
                58,
                76,
                24,
                magic_resist=13,
                speed=9,
                precision=13,
                evasion=0,
                crit_chance=0.06,
                crit_damage=1.6,
                armor_penetration=9,
            ),
            gold_min=730,
            gold_max=870,
        )

    def perform_turn(self, player) -> None:
        # Un turno de cada cinco, de media, pronuncia una proclama en vez de
        # atacar: no hay forma de esquivarla (mismo patrón que el terremoto
        # del Gólem de Piedra).
        if random.random() < 0.2:
            self._proclamation(player)
        else:
            super().perform_turn(player)

    def _proclamation(self, player) -> None:
        print(console.colorize(f"¡{self.name} pronuncia una sentencia que no admite réplica!", console.Fore.RED))

        damage = self.get_attack_damage()
        final_damage = player.take_damage(damage, armor_penetration=self.stats.armor_penetration)
        print(
            f"La proclama hace {console.colorize(str(final_damage), console.Fore.RED)} de daño. "
            f"{console.colorize('(imposible de esquivar)', console.Fore.BLACK, bright=True)}"
        )

    def drop_item(self) -> list:
        items = []
        if random.random() <= 0.55:
            items.append(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20))
        if random.random() <= 0.3:
            items.append(
                Material(
                    "Eco de Proclama",
                    "Sigue vibrando en el aire mucho después de haberse pronunciado.",
                    46,
                    rarity="Raro",
                )
            )
        if random.random() <= 0.08:
            items.append(Weapon("Cetro del Heraldo", "No necesita filo; solo necesita ser señalado.", 55, 37))
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Hombreras de Heraldo",
                    "Talladas con un sello que nadie ha sabido leer en voz alta.",
                    76,
                    slot="hombreras",
                    precision=8,
                )
            )
        return items
