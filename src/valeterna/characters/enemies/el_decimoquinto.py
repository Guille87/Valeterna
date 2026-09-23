import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats, resolve_hit
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class ElDecimoquinto(Enemy):
    DESCRIPTION = (
        "Catorce nombres se grabaron enteros en el puntal. El decimoquinto se quedó a medio hacer — solo una K, "
        "y el corte de un cuchillo que se detuvo a tiempo. La mina terminó lo que esa mano no pudo."
    )
    SIGNATURE = "El Nombre Sin Terminar: se cura con la carga del mineral y descarga rayos que pueden paralizar."
    ELEMENTS_DEALT = frozenset({"rayo"})
    INFLICTS = frozenset({"paralizado"})

    # Guardián del Cañón del Trueno: hecho de piedra, rayo y un nombre que
    # nunca se terminó de grabar — lo sagrado es lo único que lo alcanza; su
    # propio elemento ya no le hace nada nuevo.
    WEAKNESSES = frozenset({"sagrado"})
    RESISTANCES = frozenset({"rayo"})

    ENCOUNTER_KIND = "guardian"
    ENCOUNTER_LINE = (
        "El puntal de la mina se resquebraja del todo. La última letra a medio grabar por fin se completa, y algo "
        "que llevaba catorce nombres esperando compañía se pone en pie."
    )
    TAUNT_LINES = (
        "Nunca terminé mi nombre. Terminaré el tuyo por ti.",
        "Catorce promesas de piedra. Tú serás la decimoquinta.",
        "El cuchillo se detuvo a tiempo. Yo no lo haré.",
    )

    def __init__(self):
        super().__init__(
            "El Decimoquinto",
            Stats(
                975,
                975,
                34,
                46,
                20,
                magic_resist=10,
                speed=12,
                precision=13,
                evasion=5,
                crit_chance=0.09,
                crit_damage=1.7,
                armor_penetration=7,
                magic_penetration=4,
            ),
            gold_min=340,
            gold_max=405,
        )

    def perform_turn(self, player) -> None:
        # Autocuración bajo el 40% de vida, mismo umbral que El Enraizado y El Anegado.
        if self.stats.health <= (self.stats.max_health * 0.4) and random.random() < 0.35:
            self._self_heal()
            return

        self._lightning_strike(player)

    def _self_heal(self) -> None:
        healed = self.heal(random.randint(40, 60))
        if healed <= 0:
            print(f"{console.colorize(self.name, console.Fore.MAGENTA)} busca carga en la roca, pero ya no queda nada.")
            return
        print(
            f"{console.colorize(self.name, console.Fore.MAGENTA)} absorbe la carga del mineral que lo formó. "
            f"{console.colorize(f'+{healed} HP', console.Fore.GREEN)}."
        )

    def _lightning_strike(self, player) -> None:
        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(
                f"{console.colorize(self.name, console.Fore.RED)} descarga un rayo, pero "
                f"{console.colorize(player.name, console.Fore.GREEN)} logra esquivarlo."
            )
            return

        is_crit = random.random() < self.stats.crit_chance
        damage = self.get_max_attack_damage() if is_crit else self.get_attack_damage()
        if is_crit:
            damage = int(damage * self.stats.crit_damage)

        final_damage = player.take_damage(damage, armor_penetration=self.stats.armor_penetration, element="rayo")
        print(
            f"{console.colorize(self.name, console.Fore.RED)} descarga un rayo y hace "
            f"{console.colorize(str(final_damage), console.Fore.RED)} de daño."
            f"{console.crit_suffix(is_crit)}"
        )

        if random.random() < 0.3:
            player.apply_status("paralizado", 1)
            print(console.colorize("¡La descarga te deja paralizado!", console.Fore.YELLOW))

    def drop_item(self) -> list:
        items = []
        if random.random() <= 0.6:
            items.append(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20))
        if random.random() <= 0.3:
            items.append(
                Material(
                    "Nombre a Medio Grabar",
                    "Un fragmento de puntal con una sola letra tallada: una K.",
                    28,
                    rarity="Raro",
                )
            )
        if random.random() <= 0.1:
            items.append(
                Weapon(
                    "Cuchillo Detenido",
                    "El corte se detuvo a mitad de una letra. Sigue afilado igual.",
                    38,
                    26,
                    element="rayo",
                )
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Anillo del Decimoquinto",
                    "Frío al tacto, salvo cuando truena.",
                    44,
                    slot="anillo",
                    crit_damage=0.10,
                )
            )
        return items
