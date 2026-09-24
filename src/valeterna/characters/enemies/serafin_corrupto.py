import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats, resolve_hit
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class SerafinCorrupto(Enemy):
    DESCRIPTION = "Sirvió antes de la Brecha. Sirve ahora al mismo altar, solo que el altar ha cambiado de dueño."
    SIGNATURE = "Gracia invertida: se cura con luz vuelta del revés y puede maldecir tu armadura."
    ELEMENTS_DEALT = frozenset({"oscuridad"})
    INFLICTS = frozenset({"maldicion"})
    ENCOUNTER_LINE = "Un resplandor equivocado cruza la Catedral rota. Un Serafín Corrupto despliega alas que ya no deberían ser suyas."

    # Tier 5 de la Ciudadela (primer élite): lo sagrado de verdad todavía
    # reconoce la impostura y la castiga; su propia corrupción lo protege
    # de la oscuridad.
    WEAKNESSES = frozenset({"sagrado"})
    RESISTANCES = frozenset({"oscuridad"})

    def __init__(self):
        super().__init__(
            "Serafín Corrupto",
            Stats(
                1405,
                1405,
                48,
                63,
                18,
                magic_resist=16,
                speed=12,
                precision=15,
                evasion=8,
                crit_chance=0.09,
                crit_damage=1.7,
                magic_penetration=9,
            ),
            gold_min=610,
            gold_max=725,
        )

    def perform_turn(self, player) -> None:
        # Autocuración bajo la mitad de vida, mismo patrón que otros
        # autocuradores de la cadena.
        if self.stats.health <= (self.stats.max_health * 0.5) and random.random() < 0.3:
            self._self_heal()
            return

        # Uno de cada cuatro turnos, de media, maldice en vez de atacar.
        if random.random() < 0.25:
            self._cast_curse(player)
        else:
            self._dark_grace(player)

    def _self_heal(self) -> None:
        healed = self.heal(random.randint(50, 75))
        if healed <= 0:
            print(f"{console.colorize(self.name, console.Fore.MAGENTA)} extiende las alas, pero no llega nada.")
            return
        print(
            f"{console.colorize(self.name, console.Fore.MAGENTA)} invierte su propia luz sobre la herida. "
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
            f"{console.colorize(self.name, console.Fore.MAGENTA)} traza un símbolo invertido en el aire. "
            f"{console.colorize('¡Maldito! -4 de armadura durante 3 turnos.', console.Fore.MAGENTA)}"
        )

    def _dark_grace(self, player) -> None:
        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(
                f"{console.colorize(self.name, console.Fore.MAGENTA)} lanza un rayo de gracia invertida, pero "
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
            f"{console.colorize(self.name, console.Fore.MAGENTA)} lanza un rayo de gracia invertida y hace "
            f"{console.colorize(str(final_damage), console.Fore.MAGENTA)} de daño."
            f"{console.crit_suffix(is_crit)}"
        )

    def drop_item(self) -> list:
        items = []
        if random.random() <= 0.5:
            items.append(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20))
        if random.random() <= 0.3:
            items.append(
                Material("Pluma Invertida", "Blanca por un lado, negra por el otro; no se decide.", 41, rarity="Raro")
            )
        if random.random() <= 0.1:
            items.append(
                Weapon(
                    "Filo de Gracia Invertida",
                    "Se forjó bendecido y se corrompió antes de enfriarse.",
                    50,
                    34,
                    element="oscuridad",
                )
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Amuleto de Serafín",
                    "Un halo pequeño, doblado hasta casi partirse.",
                    70,
                    slot="amuleto",
                    magic_resist=13,
                )
            )
        return items
