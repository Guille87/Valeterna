import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats, resolve_hit
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class DruidaCorrupto(Enemy):
    DESCRIPTION = "Guardaba el equilibrio del Bosque antes de que los susurros le enseñaran una versión distinta."
    SIGNATURE = "Corrupción viva: se cura cuando está malherido y puede maldecir tu armadura."
    ELEMENTS_DEALT = frozenset({"oscuridad"})
    INFLICTS = frozenset({"maldicion"})
    ENCOUNTER_KIND = "elite"
    ENCOUNTER_LINE = "Las ramas se apartan solas. Un Druida Corrupto avanza entre ellas, y el bosque entero calla."
    TAUNT_LINES = (
        "La corrupción no se cura. Solo se extiende.",
        "Ya sentiste mi maldición una vez. Esta será peor.",
    )

    # Tier 5 del Bosque (GDD §4.1: primer élite): domina una magia corrupta,
    # pero lo sagrado todavía puede purgarla.
    WEAKNESSES = frozenset({"sagrado"})
    RESISTANCES = frozenset({"oscuridad"})

    def __init__(self):
        super().__init__(
            "Druida Corrupto",
            Stats(
                260,
                260,
                23,
                31,
                4,
                magic_resist=6,
                speed=13,
                precision=12,
                evasion=5,
                crit_chance=0.08,
                crit_damage=1.6,
                magic_penetration=3,
            ),
            gold_min=80,
            gold_max=100,
        )

    def perform_turn(self, player) -> None:
        # Autocuración bajo la mitad de vida, igual que el Chamán Goblin.
        if self.stats.health <= (self.stats.max_health * 0.5) and random.random() < 0.3:
            self._self_heal()
            return

        # Uno de cada cuatro turnos, de media, maldice en vez de atacar.
        if random.random() < 0.25:
            self._cast_curse(player)
        else:
            self._corrupt_bolt(player)

    def _self_heal(self) -> None:
        healed = self.heal(random.randint(20, 32))
        if healed <= 0:
            print(f"{console.colorize(self.name, console.Fore.MAGENTA)} extiende la mano, pero nada responde.")
            return
        print(
            f"{console.colorize(self.name, console.Fore.MAGENTA)} absorbe la savia negra del suelo. "
            f"{console.colorize(f'+{healed} HP', console.Fore.GREEN)}."
        )

    def _cast_curse(self, player) -> None:
        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(
                f"{console.colorize(self.name, console.Fore.MAGENTA)} intenta maldecir a "
                f"{console.colorize(player.name, console.Fore.GREEN)}, pero falla."
            )
            return

        player.apply_status("maldicion", duration=3, power=3)
        print(
            f"{console.colorize(self.name, console.Fore.MAGENTA)} traza un símbolo con savia negra. "
            f"{console.colorize('¡Maldito! -3 de armadura durante 3 turnos.', console.Fore.MAGENTA)}"
        )

    def _corrupt_bolt(self, player) -> None:
        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(
                f"{console.colorize(self.name, console.Fore.MAGENTA)} lanza un zarcillo oscuro, pero "
                f"{console.colorize(player.name, console.Fore.GREEN)} lo esquiva."
            )
            return

        is_crit = random.random() < self.stats.crit_chance
        damage = self.get_max_attack_damage() if is_crit else self.get_attack_damage()
        if is_crit:
            damage = int(damage * self.stats.crit_damage)

        final_damage = player.take_damage(
            damage, is_magical=True, magic_penetration=self.stats.magic_penetration, element="oscuridad"
        )
        print(
            f"{console.colorize(self.name, console.Fore.MAGENTA)} lanza un zarcillo oscuro y hace "
            f"{console.colorize(str(final_damage), console.Fore.MAGENTA)} de daño."
            f"{console.crit_suffix(is_crit)}"
        )

    def drop_item(self) -> list:
        items = []
        if random.random() <= 0.5:
            items.append(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20))
        if random.random() <= 0.3:
            items.append(
                Material("Savia Corrupta", "Negra y espesa; huele a tierra removida y a algo más.", 8, rarity="Común")
            )
        if random.random() <= 0.1:
            items.append(Weapon("Vara Retorcida", "Una rama torcida sobre sí misma varias veces.", 25, 17))
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Amuleto de Corteza",
                    "Corteza viva tallada en forma de ojo cerrado.",
                    26,
                    slot="amuleto",
                    magic_resist=4,
                )
            )
        return items
