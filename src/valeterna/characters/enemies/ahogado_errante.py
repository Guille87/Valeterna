import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class AhogadoErrante(Enemy):
    DESCRIPTION = "El agua tiene memoria y devuelve a los suyos por la noche, empapados y con hambre. Este es uno."
    SIGNATURE = "Vuelve del agua: si ya lo has vencido antes, puede emboscarte de nuevo al empezar el combate."
    ELEMENTS_DEALT = frozenset()
    INFLICTS = frozenset()
    ENCOUNTER_LINE = "Una silueta hinchada emerge del agua turbia, tambaleándose. Un Ahogado Errante viene a por ti."

    # Tier 3 de la Ciénaga: un cadáver que camina no le teme a nada salvo a lo
    # que lo devolvería a descansar de verdad.
    WEAKNESSES = frozenset({"sagrado"})

    def __init__(self):
        super().__init__(
            "Ahogado Errante",
            Stats(
                480,
                480,
                21,
                29,
                12,
                magic_resist=2,
                speed=11,
                precision=9,
                evasion=3,
                crit_chance=0.06,
                crit_damage=1.5,
                armor_penetration=4,
            ),
            gold_min=170,
            gold_max=210,
        )
        # Igual que el Goblin y el Lobo Umbrío: solo emboscará una vez lo hayas
        # derrotado antes.
        self.ambush_done = False

    def check_ambush(self, player, defeated_enemies: list | None = None) -> bool:
        if not defeated_enemies or self.name not in defeated_enemies:
            return False
        if not self.ambush_done and random.random() <= 0.35:
            self.ambush_done = True
            damage = self.get_attack_damage() + 6
            final_dmg = player.take_damage(damage, armor_penetration=self.stats.armor_penetration)
            print(
                f"\n¡{console.colorize('EMBOSCADA!', console.Fore.YELLOW)} El {self.name} sale del agua y te hace "
                f"{console.colorize(str(final_dmg), console.Fore.RED)} de daño."
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
                    "Trapo Empapado", "Nunca llega a secarse del todo, sin importar cuánto pase.", 9, rarity="Común"
                )
            )
        if random.random() <= 0.1:
            items.append(Weapon("Puño Ahogado", "Frío y pesado, como si todavía arrastrara agua consigo.", 22, 14))
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Yelmo Hinchado",
                    "Se ha deformado con el agua, pero sigue protegiendo igual de bien.",
                    30,
                    slot="casco",
                    max_health=22,
                )
            )
        return items
