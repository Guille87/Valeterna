import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import RegenPotion
from valeterna.ui import console


class Troll(Enemy):
    DESCRIPTION = "Criatura de la que hasta el bosque huye: lo que le cortas, se le vuelve a formar."
    SIGNATURE = "Regeneración: recupera vida al final de cada turno."
    ELEMENTS_DEALT = frozenset()
    INFLICTS = frozenset()
    ENCOUNTER_LINE = "Un Troll se levanta pesadamente, con heridas que ya se están cerrando solas."

    # El fuego es lo único que impide que se regenere de verdad.
    WEAKNESSES = frozenset({"fuego"})

    def __init__(self):
        super().__init__(
            "Troll",
            Stats(
                342,
                342,
                16,
                25,
                4,
                magic_resist=1,
                speed=10,
                precision=3,
                evasion=0,
                crit_chance=0.03,
                crit_damage=1.5,
                regen=10,
            ),
            gold_min=42,
            gold_max=58,
        )

    def on_turn_end(self) -> None:
        """Habilidad especial: regeneración aleatoria alrededor de su stat de
        regeneración (el Troll es de los pocos enemigos "aptos" para esto)."""
        if self.is_alive() and self.stats.health < self.stats.max_health:
            healed = self.heal(random.randint(self.stats.regen - 5, self.stats.regen + 5))
            if healed > 0:
                console.success(f"✨ El Troll gruñe mientras sus heridas se cierran (+{healed} HP).")

    def drop_item(self) -> list:
        items = []
        # 8% Maza de Piedra (drop más bajo a propósito)
        if random.random() <= 0.08:
            items.append(Weapon("Maza de Piedra", "Un bloque de granito atado a un tronco. Pesada y brutal.", 15, 17))

        # 70% Poción de Regeneración
        if random.random() <= 0.7:
            items.append(
                RegenPotion(
                    "Poción de Regeneración", "Un brebaje verde que burbujea. Cura 10 HP durante 3 turnos.", 8, 10, 3
                )
            )

        if random.random() <= 0.05:
            items.append(
                Material(
                    "Piel de Troll",
                    "Una piel gruesa y rugosa que parece pulsar con vida propia. Muy valiosa para un sastre.",
                    150,
                    rarity="Legendario",
                )
            )

        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Hombreras de Troll",
                    "Placas de hueso trolluno unidas a la piel; se regeneran casi tan rápido como su dueño original.",
                    25,
                    slot="hombreras",
                    precision=3,
                    defense=3,
                    regen=2,
                )
            )
        return items
