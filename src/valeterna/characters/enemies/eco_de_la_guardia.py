import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class EcoDeLaGuardia(Enemy):
    DESCRIPTION = "«Yo estaba de guardia en la puerta, y viví.» Este no vivió. Pero sigue de guardia igual."
    SIGNATURE = "Puesto eterno: si ya lo has vencido antes, puede emboscarte de nuevo al empezar el combate."
    ELEMENTS_DEALT = frozenset()
    INFLICTS = frozenset()
    ENCOUNTER_LINE = "Una silueta armada monta guardia frente a una puerta que ya no lleva a ningún sitio. Un Eco de la Guardia no la abandona."

    def __init__(self):
        super().__init__(
            "Eco de la Guardia",
            Stats(
                1535,
                1535,
                52,
                69,
                14,
                magic_resist=9,
                speed=11,
                precision=13,
                evasion=6,
                crit_chance=0.07,
                crit_damage=1.6,
                armor_penetration=7,
            ),
            gold_min=640,
            gold_max=765,
        )
        # Igual que el resto de emboscadores de la cadena: solo emboscará
        # una vez lo hayas derrotado antes.
        self.ambush_done = False

    def check_ambush(self, player, defeated_enemies: list | None = None) -> bool:
        if not defeated_enemies or self.name not in defeated_enemies:
            return False
        if not self.ambush_done and random.random() <= 0.35:
            self.ambush_done = True
            damage = self.get_attack_damage() + 12
            final_dmg = player.take_damage(damage, armor_penetration=self.stats.armor_penetration)
            print(
                f"\n¡{console.colorize('PUESTO!', console.Fore.YELLOW)} El {self.name} no ha abandonado su guardia "
                f"y te hace {console.colorize(str(final_dmg), console.Fore.RED)} de daño."
            )
            return True
        return False

    def drop_item(self) -> list:
        items = []
        if random.random() <= 0.5:
            items.append(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20))
        if random.random() <= 0.3:
            items.append(
                Material(
                    "Insignia de Guardia",
                    "El esmalte se ha ido, pero el metal de debajo sigue firme.",
                    42,
                    rarity="Raro",
                )
            )
        if random.random() <= 0.1:
            items.append(
                Weapon(
                    "Alabarda de Puesto",
                    "Lleva tanto tiempo clavada en el mismo sitio que ya no recuerda moverse.",
                    51,
                    35,
                )
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Botas de Puesto",
                    "El barro las ha fijado al suelo tantas veces que ya no importa.",
                    72,
                    slot="botas",
                    speed=6,
                )
            )
        return items
