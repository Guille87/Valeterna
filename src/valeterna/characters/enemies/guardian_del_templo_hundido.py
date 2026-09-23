import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class GuardianDelTemploHundido(Enemy):
    DESCRIPTION = "Tallado en la misma piedra que el templo que custodia. Lleva de pie desde antes de que se hundiera."
    SIGNATURE = "Golpe de piedra y coral: de vez en cuando ataca con un golpe imposible de esquivar."
    ELEMENTS_DEALT = frozenset()
    INFLICTS = frozenset()
    ENCOUNTER_LINE = (
        "Entre las columnas hundidas, una figura de piedra cubierta de coral se despega de la pared. "
        "El Guardián del Templo Hundido todavía cumple su turno."
    )

    # Tier 9 de la Ciénaga (tercer élite): un centinela de piedra sagrada
    # profanada, pero centinela al fin — la parálisis no encuentra nada vivo
    # a lo que aferrarse.
    WEAKNESSES = frozenset({"sagrado"})
    IMMUNE_STATUSES = frozenset({"paralizado"})

    def __init__(self):
        super().__init__(
            "Guardián del Templo Hundido",
            Stats(
                640,
                640,
                28,
                38,
                22,
                magic_resist=6,
                speed=9,
                precision=9,
                evasion=0,
                crit_chance=0.06,
                crit_damage=1.6,
                armor_penetration=7,
            ),
            gold_min=210,
            gold_max=250,
        )

    def perform_turn(self, player) -> None:
        # Un turno de cada cinco, de media, ataca con un golpe de piedra y
        # coral que no hay forma de esquivar (mismo patrón que el terremoto
        # del Gólem de Piedra y el golpe de raíces del Ent Corrompido).
        if random.random() < 0.2:
            self._stone_strike(player)
        else:
            super().perform_turn(player)

    def _stone_strike(self, player) -> None:
        print(console.colorize(f"¡{self.name} descarga todo su peso de piedra!", console.Fore.RED))

        damage = self.get_attack_damage()
        final_damage = player.take_damage(damage, armor_penetration=self.stats.armor_penetration)
        print(
            f"El golpe hace {console.colorize(str(final_damage), console.Fore.RED)} de daño. "
            f"{console.colorize('(imposible de esquivar)', console.Fore.BLACK, bright=True)}"
        )

    def drop_item(self) -> list:
        items = []
        if random.random() <= 0.55:
            items.append(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20))
        if random.random() <= 0.3:
            items.append(
                Material(
                    "Fragmento de Coral Negro", "Duro como la piedra, ramificado como algo vivo.", 15, rarity="Raro"
                )
            )
        if random.random() <= 0.08:
            items.append(
                Weapon("Puño de Coral", "Un guantelete tallado en el mismo material que el propio guardián.", 29, 20)
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Placa de Coral Negro",
                    "Losas de piedra y coral fundidas en una sola pieza.",
                    40,
                    slot="peto",
                    defense=13,
                    max_health=20,
                )
            )
        return items
