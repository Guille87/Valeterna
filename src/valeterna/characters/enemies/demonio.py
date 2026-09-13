import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats, resolve_hit
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class Demonio(Enemy):
    # Demonio clásico: lo sagrado lo hiere de verdad; la oscuridad es su
    # elemento natal, pero (a diferencia del Nigromante) no domina del todo.
    WEAKNESSES = frozenset({"sagrado"})
    RESISTANCES = frozenset({"oscuridad"})

    def __init__(self):
        super().__init__(
            "Demonio",
            Stats(
                420,
                420,
                58,
                76,
                10,
                magic_resist=10,
                speed=27,
                precision=13,
                evasion=8,
                crit_chance=0.10,
                crit_damage=1.7,
                armor_penetration=20,
                magic_penetration=6,
            ),
            gold_min=160,
            gold_max=210,
        )

    def perform_turn(self, player) -> None:
        roll = random.random()
        if roll < 0.2:
            self._summon_lesser_demon(player)
        elif roll < 0.4:
            self._cast_confusion(player)
        else:
            self._claw_attack(player)

    def _claw_attack(self, player) -> None:
        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(
                f"{console.colorize(self.name, console.Fore.RED)} ataca, pero "
                f"{console.colorize(player.name, console.Fore.GREEN)} lo esquiva."
            )
            return

        damage = self.get_attack_damage()
        is_crit = random.random() < self.stats.crit_chance
        if is_crit:
            damage = int(damage * self.stats.crit_damage)

        final_damage = player.take_damage(damage, armor_penetration=self.stats.armor_penetration)

        if is_crit:
            print(console.colorize("¡Golpe crítico!", console.Fore.YELLOW, bright=True))
        print(
            f"{console.colorize(self.name, console.Fore.RED)} zarpazo llameante: "
            f"{console.colorize(str(final_damage), console.Fore.RED)} de daño."
        )

    def _summon_lesser_demon(self, player) -> None:
        print(
            console.colorize(
                f"{self.name} abre una grieta llameante... ¡un demonio menor salta a través de ella!", console.Fore.RED
            )
        )

        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(f"El demonio menor ataca, pero {console.colorize(player.name, console.Fore.GREEN)} lo esquiva.")
            return

        damage = self.get_attack_damage()
        final_damage = player.take_damage(damage, is_magical=True, magic_penetration=self.stats.magic_penetration)
        print(f"El demonio menor hace {console.colorize(str(final_damage), console.Fore.MAGENTA)} de daño ígneo.")

    def _cast_confusion(self, player) -> None:
        """Confusión: reduce la evasión efectiva del jugador durante unos turnos."""
        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(
                f"{console.colorize(self.name, console.Fore.RED)} intenta confundir a "
                f"{console.colorize(player.name, console.Fore.GREEN)}, pero falla."
            )
            return

        player.apply_status("confusion", duration=3, power=5)
        print(
            f"{console.colorize(self.name, console.Fore.RED)} susurra palabras que retuercen la mente. "
            f"{console.colorize('¡Confundido! -5 de evasión durante 3 turnos.', console.Fore.RED)}"
        )

    def drop_item(self) -> list:
        items = []
        if random.random() <= 0.5:
            items.append(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20))
        if random.random() <= 0.3:
            items.append(
                Material("Ceniza Infernal", "Restos calcinados que aún arden sin consumirse.", 45, rarity="Raro")
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Coraza Demoníaca",
                    "Placas de hueso ennegrecido, calientes al tacto.",
                    80,
                    slot="peto",
                    defense=23,
                    magic_resist=6,
                    max_health=30,
                )
            )
        if random.random() <= 0.08:
            items.append(
                Weapon(
                    "Garra Infernal", "Arrancada de un demonio menor; sigue chisporroteando.", 45, 29, element="fuego"
                )
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Perneras Infernales",
                    "Cubiertas de brasas que nunca terminan de apagarse.",
                    60,
                    slot="perneras",
                    evasion=6,
                    defense=10,
                    magic_resist=4,
                )
            )
        return items
