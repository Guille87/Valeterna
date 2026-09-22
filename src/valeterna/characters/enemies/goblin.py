import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats
from valeterna.items.equipment import Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class Goblin(Enemy):
    DESCRIPTION = (
        "Carroñero de piel verde y colmillos amarillos. Aprende de las palizas: cuando ya lo has vencido, te acecha."
    )
    SIGNATURE = "Emboscada: si ya lo has derrotado antes, puede atacarte por sorpresa antes de empezar el combate."
    ELEMENTS_DEALT = frozenset()
    INFLICTS = frozenset()

    def __init__(self):
        # health, max_health, min_atk, max_atk, defense
        super().__init__(
            "Goblin",
            Stats(
                40,
                40,
                8,
                12,
                2,
                magic_resist=0,
                speed=11,
                precision=5,
                evasion=3,
                crit_chance=0.05,
                crit_damage=1.6,
                armor_penetration=1,
            ),
            gold_min=4,
            gold_max=6,
        )
        self.ambush_done = 0  # Añadimos contador de turnos

    def check_ambush(self, player, defeated_enemies: list | None = None) -> bool:
        """Intenta realizar un ataque gratuito antes de que empiece la pelea.

        El Goblin es el primer enemigo del juego: no embosca hasta que el
        jugador lo ha derrotado al menos una vez (la primera pelea es limpia).
        """
        if not defeated_enemies or self.name not in defeated_enemies:
            return False
        if not self.ambush_done and random.random() <= 0.4:
            self.ambush_done = True
            damage = self.get_attack_damage() + 5
            final_dmg = player.take_damage(damage)
            print(
                f"\n¡{console.colorize('EMBOSCADA!', console.Fore.YELLOW)} El {self.name} sale de los "
                f"arbustos y te hace {console.colorize(str(final_dmg), console.Fore.RED)} de daño."
            )
            return True
        return False

    def perform_turn(self, player) -> None:
        # El turno normal siempre es el ataque base
        super().perform_turn(player)

    def drop_item(self) -> list:
        items = []
        if random.random() <= 0.1:
            items.append(Weapon("Espada Goblin", "Una hoja mellada y cubierta de herrumbre que aún corta", 5, 4))
        if random.random() <= 0.8:
            items.append(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20))
        if random.random() <= 0.25:
            items.append(
                Material(
                    "Colmillo de Goblin", "Un colmillo curvo y afilado, típico de estas criaturas.", 3, rarity="Común"
                )
            )
        return items
