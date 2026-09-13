import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats
from valeterna.items.equipment import Armor
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class Skeleton(Enemy):
    # No-muerto: lo sagrado le hace mella, y sin sangre ni órganos el veneno le
    # afecta poco y no puede envenenarle ni hacerle sangrar en absoluto.
    WEAKNESSES = frozenset({"sagrado"})
    RESISTANCES = frozenset({"veneno"})
    IMMUNE_STATUSES = frozenset({"veneno", "sangrado"})

    def __init__(self):
        # Los esqueletos tienen buena defensa pero poca vida
        super().__init__(
            "Esqueleto",
            Stats(
                60, 60, 10, 15, 5, magic_resist=2, speed=8, precision=8, evasion=2, crit_chance=0.05, crit_damage=1.5
            ),
            gold_min=10,
            gold_max=14,
        )
        self.has_revived = False

    def take_damage(
        self,
        amount: int,
        defeated_enemies: list | None = None,
        element: str | None = None,
        is_magical: bool = False,
        armor_penetration: int = 0,
        magic_penetration: int = 0,
    ) -> int:
        # Calculamos el daño normal usando la lógica de la clase padre
        final_damage = super().take_damage(
            amount,
            element=element,
            is_magical=is_magical,
            armor_penetration=armor_penetration,
            magic_penetration=magic_penetration,
        )

        # LÓGICA DE REANIMACIÓN
        # Si la vida llega a 0 y aún no ha revivido...
        if self.stats.health <= 0 and not self.has_revived:
            self.has_revived = True
            # Revive con la mitad de su vida máxima
            self.stats.health = self.stats.max_health // 2

            print(
                f"\n{console.colorize('☠️  ¡Los huesos del Esqueleto se reensamblan mágicamente!', console.Fore.WHITE)}"
            )

            # Verificamos si mostramos la vida o no
            # Si defeated_enemies es None o el nombre no está en la lista, ocultamos
            if defeated_enemies and self.name in defeated_enemies:
                console.info(f"El Esqueleto ha revivido con {self.stats.health} HP.")
            else:
                print(console.colorize("El Esqueleto ha revivido con ??? HP.", console.Fore.BLACK, bright=True))
            return final_damage

        return final_damage

    def perform_turn(self, player) -> None:
        super().perform_turn(player)

    def drop_item(self) -> list:
        items = []
        # 10% de soltar un casco de hueso
        if random.random() <= 0.1:
            items.append(
                Armor(
                    "Casco de Hueso",
                    "Hecho con restos de otros guerreros",
                    8,
                    slot="casco",
                    max_health=15,
                    crit_chance=0.03,
                )
            )
        # 50% de soltar una poción de salud
        if random.random() <= 0.5:
            items.append(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20))
        # 25% de soltar un fragmento de hueso
        if random.random() <= 0.25:
            items.append(
                Material("Fragmento de Hueso", "Un resto óseo todavía impregnado de magia residual.", 4, rarity="Común")
            )
        # 8% de soltar unos guantes óseos
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Guantes Óseos",
                    "Falanges ajenas ensartadas en un guante de cuero curtido.",
                    12,
                    slot="guantes",
                    crit_damage=0.10,
                    defense=2,
                )
            )
        return items
