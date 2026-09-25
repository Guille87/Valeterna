import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class CangrejoAcorazado(Enemy):
    DESCRIPTION = "Su caparazón ha crecido tanto que ya no cabe entero bajo el agua. No le hace falta huir de nada."
    SIGNATURE = "Tenaza implacable: de vez en cuando cierra la pinza con una fuerza imposible de esquivar."
    ELEMENTS_DEALT = frozenset()
    INFLICTS = frozenset()
    ENCOUNTER_KIND = "elite"
    ENCOUNTER_LINE = "El barro se abre y un Cangrejo Acorazado emerge, tan ancho como el propio camino."
    TAUNT_LINES = (
        "Mi caparazón ya aguantó todo lo que le lanzaste.",
        "No hace falta huir de nada. Tampoco de ti.",
    )

    def __init__(self):
        super().__init__(
            "Cangrejo Acorazado",
            Stats(
                775,
                775,
                24,
                32,
                20,
                magic_resist=3,
                speed=7,
                precision=7,
                evasion=0,
                crit_chance=0.05,
                crit_damage=1.5,
                armor_penetration=6,
            ),
            gold_min=190,
            gold_max=230,
        )

    def perform_turn(self, player) -> None:
        # Un turno de cada cinco, de media, cierra la tenaza en vez de un
        # golpe normal: no hay forma de esquivarla (mismo patrón que el
        # terremoto del Gólem de Piedra y el golpe de raíces del Ent Corrompido).
        if random.random() < 0.2:
            self._pincer_crush(player)
        else:
            super().perform_turn(player)

    def _pincer_crush(self, player) -> None:
        print(console.colorize(f"¡{self.name} cierra su tenaza con todo su peso!", console.Fore.RED))

        damage = self.get_attack_damage()
        final_damage = player.take_damage(damage, armor_penetration=self.stats.armor_penetration)
        print(
            f"La tenaza aplasta y hace {console.colorize(str(final_damage), console.Fore.RED)} de daño. "
            f"{console.colorize('(imposible de esquivar)', console.Fore.BLACK, bright=True)}"
        )

    def drop_item(self) -> list:
        items = []
        if random.random() <= 0.5:
            items.append(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20))
        if random.random() <= 0.3:
            items.append(
                Material(
                    "Caparazón de Cangrejo",
                    "Grueso y curvo; sigue siendo duro mucho después de la muerte.",
                    11,
                    rarity="Poco común",
                )
            )
        if random.random() <= 0.08:
            items.append(
                Weapon("Tenaza Cercenadora", "Pesa tanto que hace falta usar las dos manos para blandirla.", 26, 17)
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Placa de Caparazón",
                    "Una losa curva de caparazón, moldeada para envolver el torso.",
                    35,
                    slot="peto",
                    defense=10,
                    max_health=15,
                )
            )
        return items
