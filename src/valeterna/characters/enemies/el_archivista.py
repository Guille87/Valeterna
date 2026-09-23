import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats, resolve_hit
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class ElArchivista(Enemy):
    DESCRIPTION = (
        "«No está en su estante. Alguien lo sacó antes de que yo empezara a catalogar. — S.» Fue él quien lo sacó."
    )
    SIGNATURE = "El Tomo Que Faltaba: se cura con energía arcana y puede maldecir tu armadura al golpear."
    ELEMENTS_DEALT = frozenset({"arcano"})
    INFLICTS = frozenset({"maldicion"})

    # Guardián de la Torre de los Arcanos/Necrópolis: lo sagrado es lo único
    # que perturba a quien lleva siglos escondido tras su propio sello.
    WEAKNESSES = frozenset({"sagrado"})
    RESISTANCES = frozenset({"arcano"})

    ENCOUNTER_KIND = "guardian"
    ENCOUNTER_LINE = (
        "El estante vacío de la Biblioteca deja de estar vacío. El Archivista, el que se llevó el tomo prohibido "
        "antes de que nadie empezara a catalogar nada, por fin sale a recibirte."
    )
    TAUNT_LINES = (
        "Catalogué cada ritual. Este no lo compartí con nadie.",
        "El tomo sigue cerrado. Tú no lo estarás tanto tiempo.",
        "Sella cree que perdió un libro. Perdió mucho más que eso.",
    )

    def __init__(self):
        super().__init__(
            "El Archivista",
            Stats(
                1280,
                1280,
                42,
                56,
                16,
                magic_resist=14,
                speed=12,
                precision=14,
                evasion=6,
                crit_chance=0.09,
                crit_damage=1.7,
                magic_penetration=8,
            ),
            gold_min=510,
            gold_max=610,
        )

    def perform_turn(self, player) -> None:
        # Autocuración bajo el 40% de vida, mismo umbral que los guardianes anteriores.
        if self.stats.health <= (self.stats.max_health * 0.4) and random.random() < 0.35:
            self._self_heal()
            return

        self._forbidden_bolt(player)

    def _self_heal(self) -> None:
        healed = self.heal(random.randint(45, 65))
        if healed <= 0:
            print(
                f"{console.colorize(self.name, console.Fore.MAGENTA)} busca en el tomo, pero ya no queda nada que dar."
            )
            return
        print(
            f"{console.colorize(self.name, console.Fore.MAGENTA)} pasa una página del tomo que faltaba. "
            f"{console.colorize(f'+{healed} HP', console.Fore.GREEN)}."
        )

    def _forbidden_bolt(self, player) -> None:
        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(
                f"{console.colorize(self.name, console.Fore.RED)} lanza un dardo del tomo prohibido, pero "
                f"{console.colorize(player.name, console.Fore.GREEN)} logra esquivarlo."
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
            f"{console.colorize(self.name, console.Fore.RED)} lanza un dardo del tomo prohibido y hace "
            f"{console.colorize(str(final_damage), console.Fore.RED)} de daño."
            f"{console.crit_suffix(is_crit)}"
        )

        if random.random() < 0.3:
            player.apply_status("maldicion", duration=3, power=4)
            print(
                console.colorize(
                    "¡Una cláusula del sello se cierra sobre tu armadura! -4 de armadura.", console.Fore.MAGENTA
                )
            )

    def drop_item(self) -> list:
        items = []
        if random.random() <= 0.6:
            items.append(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20))
        if random.random() <= 0.3:
            items.append(
                Material(
                    "Hoja del Tomo que Faltaba",
                    "Una sola página, arrancada a propósito del resto del libro.",
                    36,
                    rarity="Raro",
                )
            )
        if random.random() <= 0.1:
            items.append(
                Weapon(
                    "Pluma del Archivista",
                    "Sigue escribiendo sola si la dejas quieta demasiado tiempo.",
                    46,
                    31,
                    element="arcano",
                )
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Amuleto del Archivista",
                    "Un sello de biblioteca que nunca llegó a devolverse.",
                    62,
                    slot="amuleto",
                    magic_resist=11,
                )
            )
        return items
