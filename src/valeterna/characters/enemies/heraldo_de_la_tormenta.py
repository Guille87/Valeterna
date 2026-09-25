import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats, resolve_hit
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class HeraldoDeLaTormenta(Enemy):
    DESCRIPTION = (
        "Vendía mineral de tormenta a la Torre antes de entender para qué lo querían. Ahora predica lo mismo que ellos."
    )
    SIGNATURE = "Sermón de la Brecha: se cura con el propio mineral y puede maldecir tu armadura con un rayo."
    ELEMENTS_DEALT = frozenset({"rayo"})
    INFLICTS = frozenset({"maldicion"})
    ENCOUNTER_KIND = "elite"
    ENCOUNTER_LINE = (
        "Una figura envuelta en polvo de mina alza los brazos hacia la tormenta. Un Heraldo de la Tormenta te ha visto."
    )
    TAUNT_LINES = (
        "El sermón no termina hasta que alguien escucha de verdad.",
        "Ya maldije tu armadura una vez. Hoy no la llevarás mejor.",
    )

    # Tier 9 del Cañón (tercer élite): predica lo mismo que corrompió la
    # Ciénaga y el Bosque, así que lo sagrado lo purga igual de bien; su
    # propio elemento, en cambio, ya no le hace nada nuevo.
    WEAKNESSES = frozenset({"sagrado"})
    RESISTANCES = frozenset({"rayo"})

    def __init__(self):
        super().__init__(
            "Heraldo de la Tormenta",
            Stats(
                860,
                860,
                36,
                48,
                14,
                magic_resist=9,
                speed=12,
                precision=14,
                evasion=6,
                crit_chance=0.09,
                crit_damage=1.7,
                armor_penetration=6,
            ),
            gold_min=320,
            gold_max=380,
        )

    def perform_turn(self, player) -> None:
        # Autocuración bajo la mitad de vida, mismo patrón que el Chamán del Cieno.
        if self.stats.health <= (self.stats.max_health * 0.5) and random.random() < 0.3:
            self._self_heal()
            return

        # Uno de cada cuatro turnos, de media, maldice en vez de atacar.
        if random.random() < 0.25:
            self._cast_curse(player)
        else:
            self._storm_bolt(player)

    def _self_heal(self) -> None:
        healed = self.heal(random.randint(30, 48))
        if healed <= 0:
            print(f"{console.colorize(self.name, console.Fore.MAGENTA)} alza el mineral, pero ya no le queda carga.")
            return
        print(
            f"{console.colorize(self.name, console.Fore.MAGENTA)} absorbe la carga de su mineral de tormenta. "
            f"{console.colorize(f'+{healed} HP', console.Fore.GREEN)}."
        )

    def _cast_curse(self, player) -> None:
        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(
                f"{console.colorize(self.name, console.Fore.MAGENTA)} intenta maldecir a "
                f"{console.colorize(player.name, console.Fore.GREEN)}, pero falla."
            )
            return

        player.apply_status("maldicion", duration=3, power=4)
        print(
            f"{console.colorize(self.name, console.Fore.MAGENTA)} traza un símbolo con mineral de tormenta. "
            f"{console.colorize('¡Maldito! -4 de armadura durante 3 turnos.', console.Fore.MAGENTA)}"
        )

    def _storm_bolt(self, player) -> None:
        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(
                f"{console.colorize(self.name, console.Fore.MAGENTA)} lanza un rayo, pero "
                f"{console.colorize(player.name, console.Fore.GREEN)} lo esquiva."
            )
            return

        is_crit = random.random() < self.stats.crit_chance
        damage = self.get_max_attack_damage() if is_crit else self.get_attack_damage()
        if is_crit:
            damage = int(damage * self.stats.crit_damage)

        final_damage = player.take_damage(damage, armor_penetration=self.stats.armor_penetration, element="rayo")
        print(
            f"{console.colorize(self.name, console.Fore.MAGENTA)} lanza un rayo y hace "
            f"{console.colorize(str(final_damage), console.Fore.MAGENTA)} de daño."
            f"{console.crit_suffix(is_crit)}"
        )

    def drop_item(self) -> list:
        items = []
        if random.random() <= 0.5:
            items.append(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20))
        if random.random() <= 0.3:
            items.append(
                Material(
                    "Mineral Bendecido por la Brecha",
                    "Late con una carga que no es del todo eléctrica.",
                    25,
                    rarity="Raro",
                )
            )
        if random.random() <= 0.1:
            items.append(
                Weapon(
                    "Vara de Tormenta",
                    "Tallada de un puntal de mina, envuelta en filamentos metálicos.",
                    35,
                    24,
                    element="rayo",
                )
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Amuleto de Mineral",
                    "Un fragmento de mineral de tormenta engarzado en cadena.",
                    46,
                    slot="amuleto",
                    magic_resist=7,
                )
            )
        return items
