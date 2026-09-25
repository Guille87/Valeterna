import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class LoboUmbrio(Enemy):
    DESCRIPTION = "Se mueve entre las sombras de los árboles sin hacer ruido, y no olvida a quien ya lo ha herido."
    SIGNATURE = "Acecho: si ya lo has vencido antes, puede emboscarte de nuevo al empezar el combate."
    ELEMENTS_DEALT = frozenset()
    INFLICTS = frozenset()
    ENCOUNTER_LINE = "Unos ojos amarillos te siguen entre los troncos. Un Lobo Umbrío sale a tu paso."

    def __init__(self):
        super().__init__(
            "Lobo Umbrío",
            Stats(
                368,
                368,
                26,
                35,
                5,
                magic_resist=1,
                speed=13,
                precision=11,
                evasion=7,
                crit_chance=0.07,
                crit_damage=1.6,
                armor_penetration=3,
            ),
            gold_min=130,
            gold_max=165,
        )
        # Igual que el Goblin: solo emboscará una vez lo hayas derrotado antes.
        self.ambush_done = 0

    def check_ambush(self, player, defeated_enemies: list | None = None) -> bool:
        if not defeated_enemies or self.name not in defeated_enemies:
            return False
        if not self.ambush_done and random.random() <= 0.35:
            self.ambush_done = True
            damage = self.get_attack_damage() + 6
            final_dmg = player.take_damage(damage, armor_penetration=self.stats.armor_penetration)
            print(
                f"\n¡{console.colorize('ACECHO!', console.Fore.YELLOW)} El {self.name} salta desde las sombras y "
                f"te hace {console.colorize(str(final_dmg), console.Fore.RED)} de daño."
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
                    "Pelaje Umbrío",
                    "Absorbe la luz en vez de reflejarla; sigue frío mucho después de la caza.",
                    10,
                    rarity="Poco común",
                )
            )
        if random.random() <= 0.1:
            items.append(
                Weapon("Colmillos de Sombra", "Curvados y afilados, como toda la manada de la que viene.", 28, 18)
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Botas de Sombra",
                    "No hacen ruido ni sobre las hojas más secas.",
                    32,
                    slot="botas",
                    speed=2,
                )
            )
        return items
