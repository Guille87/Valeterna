import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats, resolve_hit
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class BibliotecarioErrante(Enemy):
    DESCRIPTION = (
        "Sigue catalogando pasillos que ya nadie visita. No leas en voz alta lo que él lee: algunas frases contestan."
    )
    SIGNATURE = "Lectura en voz alta: puede confundirte además de golpearte con magia arcana."
    ELEMENTS_DEALT = frozenset({"arcano"})
    INFLICTS = frozenset({"confusion"})
    ENCOUNTER_LINE = "Una figura encorvada pasa las páginas de un libro que ya no tiene dueño. Un Bibliotecario Errante alza la vista."

    # Tier 7 de la Torre (segundo élite): sirve al mismo canal que el
    # Custodio Arcano, con las mismas afinidades de estudioso.
    WEAKNESSES = frozenset({"sagrado"})
    RESISTANCES = frozenset({"arcano"})

    def __init__(self):
        super().__init__(
            "Bibliotecario Errante",
            Stats(
                1060,
                1060,
                40,
                54,
                14,
                magic_resist=10,
                speed=12,
                precision=15,
                evasion=6,
                crit_chance=0.09,
                crit_damage=1.7,
                magic_penetration=7,
            ),
            gold_min=440,
            gold_max=525,
        )

    def perform_turn(self, player) -> None:
        # Uno de cada cuatro turnos, de media, confunde en vez de atacar.
        if random.random() < 0.25:
            self._read_aloud(player)
        else:
            self._arcane_bolt(player)

    def _read_aloud(self, player) -> None:
        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(
                f"{console.colorize(self.name, console.Fore.MAGENTA)} lee un pasaje en voz alta, pero "
                f"{console.colorize(player.name, console.Fore.GREEN)} no le presta atención."
            )
            return

        player.apply_status("confusion", duration=3, power=5)
        print(
            f"{console.colorize(self.name, console.Fore.MAGENTA)} lee un pasaje en voz alta y la frase contesta. "
            f"{console.colorize('¡Confundido!', console.Fore.MAGENTA)}"
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
                    "Ficha de Préstamo",
                    "El título está raspado; no hace falta leerlo para sentirlo mirar.",
                    31,
                    rarity="Raro",
                )
            )
        if random.random() <= 0.1:
            items.append(
                Weapon(
                    "Puntero de Latón",
                    "Usado para señalar líneas que el propio bibliotecario ya no recuerda.",
                    43,
                    29,
                    element="arcano",
                )
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Anillo del Archivo",
                    "Un sello de biblioteca fundido alrededor del dedo.",
                    56,
                    slot="anillo",
                    crit_damage=0.11,
                )
            )
        return items
