import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats, resolve_hit
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class CustodioArcano(Enemy):
    DESCRIPTION = "Vigila la sección restringida desde antes de que nadie recuerde qué protegía en realidad."
    SIGNATURE = "Escudo de estudio: se repara con energía arcana y lanza dardos de la misma magia."
    ELEMENTS_DEALT = frozenset({"arcano"})
    INFLICTS = frozenset()
    ENCOUNTER_LINE = "Runas suspendidas en el aire giran hacia ti. Un Custodio Arcano despierta de su vigilia."

    # Tier 5 de la Torre (primer élite): un constructo tejido de energía
    # arcana, sin cuerpo que envenenar; el hielo, en cambio, congela el
    # circuito que lo mantiene en pie.
    WEAKNESSES = frozenset({"hielo"})
    IMMUNE_ELEMENTS = frozenset({"veneno"})
    IMMUNE_STATUSES = frozenset({"veneno"})

    def __init__(self):
        super().__init__(
            "Custodio Arcano",
            Stats(
                1065,
                1065,
                38,
                50,
                12,
                magic_resist=12,
                speed=11,
                precision=13,
                evasion=5,
                crit_chance=0.08,
                crit_damage=1.7,
                magic_penetration=6,
            ),
            gold_min=400,
            gold_max=475,
        )

    def perform_turn(self, player) -> None:
        # Autocuración bajo la mitad de vida, mismo patrón que otros
        # autocuradores de la cadena.
        if self.stats.health <= (self.stats.max_health * 0.5) and random.random() < 0.3:
            self._self_heal()
            return

        self._arcane_bolt(player)

    def _self_heal(self) -> None:
        healed = self.heal(random.randint(35, 55))
        if healed <= 0:
            print(f"{console.colorize(self.name, console.Fore.MAGENTA)} traza una runa, pero no responde nada.")
            return
        print(
            f"{console.colorize(self.name, console.Fore.MAGENTA)} reconstruye su escudo con energía arcana. "
            f"{console.colorize(f'+{healed} HP', console.Fore.GREEN)}."
        )

    def _arcane_bolt(self, player) -> None:
        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(
                f"{console.colorize(self.name, console.Fore.MAGENTA)} lanza un dardo arcano, pero "
                f"{console.colorize(player.name, console.Fore.GREEN)} lo esquiva."
            )
            return

        is_crit = random.random() < self.stats.crit_chance
        damage = self.get_max_attack_damage() if is_crit else self.get_attack_damage()
        if is_crit:
            damage = int(damage * self.stats.crit_damage)

        final_damage = player.take_damage(
            damage, is_magical=True, magic_penetration=self.stats.magic_penetration, element="arcano"
        )
        print(
            f"{console.colorize(self.name, console.Fore.MAGENTA)} lanza un dardo arcano y hace "
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
                    "Runa Suspendida", "Sigue girando muy despacio incluso separada del constructo.", 29, rarity="Raro"
                )
            )
        if random.random() <= 0.1:
            items.append(
                Weapon(
                    "Vara de Estudio",
                    "Tallada para canalizar, no para golpear; aun así, golpea bien.",
                    40,
                    27,
                    element="arcano",
                )
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Brazales de Custodio",
                    "Grabados con las mismas runas que flotaban a su alrededor.",
                    52,
                    slot="brazales",
                    crit_chance=0.06,
                )
            )
        return items
