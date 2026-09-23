import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class EntCorrompido(Enemy):
    DESCRIPTION = (
        "Fue un árbol centenario antes de que el altar lo alcanzara. Ahora camina, y no siempre en línea recta."
    )
    SIGNATURE = "Golpe de raíces: de vez en cuando ataca con un golpe imposible de esquivar."
    ELEMENTS_DEALT = frozenset()
    INFLICTS = frozenset()
    ENCOUNTER_LINE = "El suelo se abre entre las raíces de un tronco enorme. El Ent Corrompido se pone en pie."

    # Tier 9 del Bosque (tercer élite): la madera arde bien; sin nervios, no
    # hay parálisis que valga.
    WEAKNESSES = frozenset({"fuego"})
    IMMUNE_STATUSES = frozenset({"paralizado"})

    def __init__(self):
        super().__init__(
            "Ent Corrompido",
            Stats(
                430,
                430,
                24,
                32,
                16,
                magic_resist=4,
                speed=8,
                precision=8,
                evasion=0,
                crit_chance=0.05,
                crit_damage=1.6,
                armor_penetration=6,
            ),
            gold_min=155,
            gold_max=195,
        )

    def perform_turn(self, player) -> None:
        # Un turno de cada cinco, de media, ataca con un golpe de raíces que
        # brota bajo el jugador en vez de un golpe normal: no hay forma de
        # esquivarlo (mismo patrón que el terremoto del Gólem de Piedra).
        if random.random() < 0.2:
            self._root_strike(player)
        else:
            super().perform_turn(player)

    def _root_strike(self, player) -> None:
        print(console.colorize(f"¡{self.name} hunde sus raíces en el suelo!", console.Fore.RED))

        damage = self.get_attack_damage()
        final_damage = player.take_damage(damage, armor_penetration=self.stats.armor_penetration)
        print(
            f"Las raíces brotan bajo tus pies y hacen {console.colorize(str(final_damage), console.Fore.RED)} de daño. "
            f"{console.colorize('(imposible de esquivar)', console.Fore.BLACK, bright=True)}"
        )

    def drop_item(self) -> list:
        items = []
        if random.random() <= 0.5:
            items.append(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20))
        if random.random() <= 0.3:
            items.append(
                Material("Corteza Podrida", "Negra por dentro, dura como el hierro por fuera.", 12, rarity="Poco común")
            )
        if random.random() <= 0.08:
            items.append(Weapon("Rama de Guerra", "Arrancada del propio tronco; pesa como un mazo.", 30, 20))
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Placa de Corteza",
                    "Una plancha de corteza tan gruesa que ya no se distingue de una armadura.",
                    36,
                    slot="peto",
                    defense=8,
                    max_health=20,
                )
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Ramas Nudosas",
                    "Talladas en forma de hombreras; siguen creciendo muy despacio.",
                    28,
                    slot="hombreras",
                    precision=5,
                    defense=3,
                )
            )
        return items
