import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats, resolve_hit
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class GuardianOsario(Enemy):
    DESCRIPTION = "Ensamblado con los huesos de quienes sirvieron a la Torre. Ninguno de ellos lo supo."
    SIGNATURE = "Púas de hueso: a veces ataca dos veces seguidas antes de que puedas reaccionar."
    ELEMENTS_DEALT = frozenset()
    INFLICTS = frozenset()
    ENCOUNTER_LINE = (
        "Un montón de huesos apilados se reordena solo hasta formar una figura. Un Guardián Osario se yergue."
    )

    # Tier 4 de la Torre: no queda nada vivo que salvar, así que lo sagrado
    # es lo único que lo perturba.
    WEAKNESSES = frozenset({"sagrado"})

    def __init__(self):
        super().__init__(
            "Guardián Osario",
            Stats(
                1170,
                1170,
                40,
                53,
                18,
                magic_resist=4,
                speed=9,
                precision=10,
                evasion=1,
                crit_chance=0.05,
                crit_damage=1.6,
                armor_penetration=6,
            ),
            gold_min=380,
            gold_max=450,
        )

    def perform_turn(self, player) -> None:
        """Ataque normal; a veces sus púas de hueso golpean una segunda vez."""
        self._bone_strike(player, extra=False)

        if self.is_alive() and player.is_alive() and random.random() < 0.3:
            print(console.colorize("¡Otra hilera de púas de hueso golpea de inmediato!", console.Fore.GREEN))
            self._bone_strike(player, extra=True)

    def _bone_strike(self, player, extra: bool) -> None:
        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(
                f"{console.colorize(self.name, console.Fore.RED)} ataca, pero "
                f"{console.colorize(player.name, console.Fore.GREEN)} logra esquivarlo."
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
            f"{console.colorize(self.name, console.Fore.RED)} golpea con púas de hueso y hace "
            f"{console.colorize(str(final_damage), console.Fore.RED)} de daño."
            f"{console.crit_suffix(is_crit)}"
        )

    def drop_item(self) -> list:
        items = []
        if random.random() <= 0.5:
            items.append(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20))
        if random.random() <= 0.3:
            items.append(
                Material(
                    "Hueso Ensamblado",
                    "Encaja con otros huesos como si nunca hubiera sido de nadie en particular.",
                    27,
                    rarity="Poco común",
                )
            )
        if random.random() <= 0.08:
            items.append(
                Weapon("Lanza de Fémures", "Varios huesos largos atados en fila, afilados en la punta.", 39, 26)
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Peto de Osario",
                    "Costillas ajenas entrelazadas hasta formar una coraza.",
                    50,
                    slot="peto",
                    defense=14,
                    max_health=20,
                )
            )
        return items
