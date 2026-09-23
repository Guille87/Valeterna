import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class GuardianDelTomoProhibido(Enemy):
    DESCRIPTION = (
        "Custodia el hueco vacío donde debería estar «Rituales de Cierre y Apertura». Nadie lo puso ahí a propósito."
    )
    SIGNATURE = "Onda de sello: de vez en cuando libera una onda arcana imposible de esquivar."
    ELEMENTS_DEALT = frozenset()
    INFLICTS = frozenset()
    ENCOUNTER_LINE = (
        "El aire tiembla alrededor de un estante vacío. El Guardián del Tomo Prohibido se materializa ante ti."
    )

    # Tier 9 de la Torre (tercer élite): protege un sello, no un cuerpo, así
    # que lo sagrado es lo único que lo alcanza; sin nervios, no hay
    # parálisis que valga.
    WEAKNESSES = frozenset({"sagrado"})
    IMMUNE_STATUSES = frozenset({"paralizado"})

    def __init__(self):
        super().__init__(
            "Guardián del Tomo Prohibido",
            Stats(
                1695,
                1695,
                46,
                60,
                24,
                magic_resist=10,
                speed=8,
                precision=11,
                evasion=0,
                crit_chance=0.05,
                crit_damage=1.6,
                armor_penetration=9,
            ),
            gold_min=480,
            gold_max=575,
        )

    def perform_turn(self, player) -> None:
        # Un turno de cada cinco, de media, libera una onda de sello en vez
        # de atacar: no hay forma de esquivarla (mismo patrón que el
        # terremoto del Gólem de Piedra y el derrumbe del Verdugo de la Mina).
        if random.random() < 0.2:
            self._seal_wave(player)
        else:
            super().perform_turn(player)

    def _seal_wave(self, player) -> None:
        print(console.colorize(f"¡{self.name} libera la onda del sello!", console.Fore.RED))

        damage = self.get_attack_damage()
        final_damage = player.take_damage(damage, armor_penetration=self.stats.armor_penetration)
        print(
            f"La onda hace {console.colorize(str(final_damage), console.Fore.RED)} de daño. "
            f"{console.colorize('(imposible de esquivar)', console.Fore.BLACK, bright=True)}"
        )

    def drop_item(self) -> list:
        items = []
        if random.random() <= 0.55:
            items.append(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20))
        if random.random() <= 0.3:
            items.append(
                Material(
                    "Fragmento de Sello",
                    "Un trozo de aire endurecido, tallado con un símbolo incompleto.",
                    34,
                    rarity="Raro",
                )
            )
        if random.random() <= 0.08:
            items.append(Weapon("Mazo del Sello", "Cada golpe suena como una página al cerrarse de golpe.", 44, 30))
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Cinturón del Sello",
                    "El símbolo tallado se mueve muy despacio si dejas de mirarlo.",
                    60,
                    slot="cinturon",
                    defense=18,
                    max_health=25,
                )
            )
        return items
