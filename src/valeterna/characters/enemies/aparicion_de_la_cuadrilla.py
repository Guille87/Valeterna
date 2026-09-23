import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class AparicionDeLaCuadrilla(Enemy):
    DESCRIPTION = "Catorce nombres se grabaron en un puntal. Esto es lo que queda de todos ellos a la vez."
    SIGNATURE = "Vuelve a levantarse: si ya la has vencido antes, puede emboscarte de nuevo al empezar el combate."
    ELEMENTS_DEALT = frozenset()
    INFLICTS = frozenset()
    ENCOUNTER_LINE = "Catorce siluetas se funden en una sola sombra contra la pared de la mina. Emerge una Aparición de la Cuadrilla."

    def __init__(self):
        super().__init__(
            "Aparición de la Cuadrilla",
            Stats(
                855,
                855,
                32,
                43,
                12,
                magic_resist=4,
                speed=11,
                precision=10,
                evasion=4,
                crit_chance=0.06,
                crit_damage=1.6,
                armor_penetration=5,
            ),
            gold_min=280,
            gold_max=335,
        )
        # Igual que el Goblin, el Lobo Umbrío y el Ahogado Errante: solo
        # emboscará una vez lo hayas derrotado antes.
        self.ambush_done = False

    def check_ambush(self, player, defeated_enemies: list | None = None) -> bool:
        if not defeated_enemies or self.name not in defeated_enemies:
            return False
        if not self.ambush_done and random.random() <= 0.35:
            self.ambush_done = True
            damage = self.get_attack_damage() + 8
            final_dmg = player.take_damage(damage, armor_penetration=self.stats.armor_penetration)
            print(
                f"\n¡{console.colorize('EMBOSCADA!', console.Fore.YELLOW)} La {self.name} vuelve a levantarse y te "
                f"hace {console.colorize(str(final_dmg), console.Fore.RED)} de daño."
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
                    "Retal de Cuadrilla",
                    "Un jirón de ropa de mina; todavía huele a polvo de roca.",
                    21,
                    rarity="Poco común",
                )
            )
        if random.random() <= 0.1:
            items.append(Weapon("Barra de Mina", "Doblada por el derrumbe, todavía firme como palanca.", 33, 22))
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Guantes de Cuadrilla",
                    "Curtidos por años de picar roca; el cuero sigue aguantando.",
                    42,
                    slot="guantes",
                    crit_damage=0.10,
                )
            )
        return items
