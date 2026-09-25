import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats, resolve_hit
from valeterna.items.equipment import Armor
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class EnjambrePolillas(Enemy):
    DESCRIPTION = "No es una sola polilla, sino cientos, tan juntas que a veces se confunden con una sola sombra."
    SIGNATURE = "Enjambre: a veces otra polilla se suma al ataque, y su polvo puede envenenar."
    ELEMENTS_DEALT = frozenset()
    INFLICTS = frozenset({"veneno"})
    ENCOUNTER_LINE = "El aire se espesa de golpe: un Enjambre de Polillas Pálidas te ha encontrado en la oscuridad."

    # Tier 7 del Bosque (segundo élite): el fuego dispersa al enjambre entero
    # de un solo golpe; sin sangre que perder, no puede sangrar.
    WEAKNESSES = frozenset({"fuego"})
    IMMUNE_STATUSES = frozenset({"sangrado"})

    def __init__(self):
        super().__init__(
            "Enjambre de Polillas Pálidas",
            Stats(
                301,
                301,
                23,
                32,
                3,
                magic_resist=1,
                speed=17,
                precision=12,
                evasion=10,
                crit_chance=0.08,
                crit_damage=1.6,
                armor_penetration=1,
            ),
            gold_min=115,
            gold_max=145,
        )

    def perform_turn(self, player) -> None:
        """Ataque normal; a veces otra polilla se suma con un segundo golpe."""
        self._bite(player, extra=False)

        if self.is_alive() and player.is_alive() and random.random() < 0.3:
            print(console.colorize("¡Más polillas se suman a la nube!", console.Fore.GREEN))
            self._bite(player, extra=True)

    def _bite(self, player, extra: bool) -> None:
        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(
                f"{console.colorize(self.name, console.Fore.RED)} revolotea, pero "
                f"{console.colorize(player.name, console.Fore.GREEN)} lo espanta."
            )
            return

        is_crit = not extra and random.random() < self.stats.crit_chance
        damage = self.get_max_attack_damage() if is_crit else self.get_attack_damage()
        if extra:
            damage = max(1, damage // 2)
        if is_crit:
            damage = int(damage * self.stats.crit_damage)

        final_damage = player.take_damage(damage, armor_penetration=self.stats.armor_penetration)
        print(
            f"{console.colorize(self.name, console.Fore.RED)} muerde y hace "
            f"{console.colorize(str(final_damage), console.Fore.RED)} de daño."
            f"{console.crit_suffix(is_crit)}"
        )

        if random.random() < 0.25:
            player.apply_status("veneno", 2)
            print(console.colorize("¡El polvo de sus alas irrita la herida!", console.Fore.GREEN))
            reaction_msg = player.pop_status_reaction_message()
            if reaction_msg:
                print(reaction_msg)

    def drop_item(self) -> list:
        items = []
        if random.random() <= 0.5:
            items.append(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20))
        if random.random() <= 0.3:
            items.append(
                Material(
                    "Polvo de Ala Pálida",
                    "Fino como la ceniza; sigue posándose mucho después de recogerlo.",
                    8,
                    rarity="Poco común",
                )
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Guanteletes de Polvo de Ala",
                    "Impregnados del mismo polvo pálido que suelta el enjambre.",
                    28,
                    slot="guantes",
                    crit_damage=0.05,
                )
            )
        return items
