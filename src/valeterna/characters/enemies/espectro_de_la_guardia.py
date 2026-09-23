import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class EspectroDeLaGuardia(Enemy):
    DESCRIPTION = "Se levantan por turnos, como en una guardia que nunca termina. Cada noche, uno menos en la lista."
    SIGNATURE = "Guardia eterna: si ya lo has vencido antes, puede emboscarte de nuevo al empezar el combate."
    ELEMENTS_DEALT = frozenset()
    INFLICTS = frozenset()
    ENCOUNTER_LINE = (
        "Una silueta transparente se cuadra entre las losas de la Cripta. Un Espectro de la Guardia releva su turno."
    )

    # Tier 6 de la Torre: un fantasma que sigue cumpliendo su guardia, sin
    # cuerpo que lo sostenga; lo sagrado es lo único que le da descanso.
    WEAKNESSES = frozenset({"sagrado"})

    def __init__(self):
        super().__init__(
            "Espectro de la Guardia",
            Stats(
                1035,
                1035,
                36,
                48,
                10,
                magic_resist=8,
                speed=13,
                precision=11,
                evasion=6,
                crit_chance=0.07,
                crit_damage=1.6,
                armor_penetration=5,
            ),
            gold_min=420,
            gold_max=500,
        )
        # Igual que el resto de emboscadores de la cadena: solo emboscará
        # una vez lo hayas derrotado antes.
        self.ambush_done = False

    def check_ambush(self, player, defeated_enemies: list | None = None) -> bool:
        if not defeated_enemies or self.name not in defeated_enemies:
            return False
        if not self.ambush_done and random.random() <= 0.35:
            self.ambush_done = True
            damage = self.get_attack_damage() + 10
            final_dmg = player.take_damage(damage, armor_penetration=self.stats.armor_penetration)
            print(
                f"\n¡{console.colorize('RELEVO!', console.Fore.YELLOW)} El {self.name} vuelve a montar guardia y te "
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
                Material("Jirón Espectral", "Frío al tacto y ligero como si no pesara del todo.", 30, rarity="Raro")
            )
        if random.random() <= 0.1:
            items.append(
                Weapon("Lanza de Guardia", "Sigue en posición de firmes, aunque ya nadie la sostenga.", 41, 28)
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Hombreras de Guardia",
                    "El metal está frío incluso lejos de la Cripta.",
                    54,
                    slot="hombreras",
                    precision=7,
                )
            )
        return items
