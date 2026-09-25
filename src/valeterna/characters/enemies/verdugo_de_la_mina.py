import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class VerdugoDeLaMina(Enemy):
    DESCRIPTION = "Lo que la galería hizo con los cuerpos que no pudo devolver. Ya no distingue roca de hueso."
    SIGNATURE = "Derrumbe: de vez en cuando hace ceder el techo sobre ti, un golpe imposible de esquivar."
    ELEMENTS_DEALT = frozenset()
    INFLICTS = frozenset()
    ENCOUNTER_KIND = "elite"
    ENCOUNTER_LINE = "El techo de la galería cruje antes de que aparezca. El Verdugo de la Mina llena el túnel entero."
    TAUNT_LINES = (
        "El techo ya cedió una vez sobre ti. Puede volver a hacerlo.",
        "Aquí no distingo tu roca de tu hueso.",
    )

    # Tier 7 del Cañón (segundo élite): no es más que roca y huesos sin
    # descanso, así que lo sagrado es lo único que lo perturba; sin nervios,
    # tampoco hay parálisis que valga.
    WEAKNESSES = frozenset({"sagrado"})
    IMMUNE_STATUSES = frozenset({"paralizado"})

    def __init__(self):
        super().__init__(
            "Verdugo de la Mina",
            Stats(
                1085,
                1085,
                38,
                50,
                26,
                magic_resist=5,
                speed=8,
                precision=9,
                evasion=0,
                crit_chance=0.05,
                crit_damage=1.6,
                armor_penetration=8,
            ),
            gold_min=305,
            gold_max=365,
        )

    def perform_turn(self, player) -> None:
        # Un turno de cada cinco, de media, provoca un derrumbe en vez de
        # atacar: no hay forma de esquivarlo (mismo patrón que el terremoto
        # del Gólem de Piedra).
        if random.random() < 0.2:
            self._cave_in(player)
        else:
            super().perform_turn(player)

    def _cave_in(self, player) -> None:
        print(console.colorize(f"¡{self.name} hace ceder el techo de la galería!", console.Fore.RED))

        damage = self.get_attack_damage()
        final_damage = player.take_damage(damage, armor_penetration=self.stats.armor_penetration)
        print(
            f"El derrumbe hace {console.colorize(str(final_damage), console.Fore.RED)} de daño. "
            f"{console.colorize('(imposible de esquivar)', console.Fore.BLACK, bright=True)}"
        )

    def drop_item(self) -> list:
        items = []
        if random.random() <= 0.55:
            items.append(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20))
        if random.random() <= 0.3:
            items.append(
                Material(
                    "Roca Amalgamada",
                    "Roca y hueso fundidos en una sola pieza; pesa más de lo que debería.",
                    24,
                    rarity="Raro",
                )
            )
        if random.random() <= 0.08:
            items.append(Weapon("Mazo de Galería", "Un puntal entero reforjado en arma.", 36, 24))
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Cinturón de Galería",
                    "Cuerda de mina trenzada tan tensa que ya no se deshace.",
                    44,
                    slot="cinturon",
                    defense=16,
                    max_health=25,
                )
            )
        return items
