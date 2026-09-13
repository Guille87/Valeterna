import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats, resolve_hit
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class Nigromante(Enemy):
    def __init__(self):
        # Hechicero oscuro: su ataque habitual es mágico, no físico.
        super().__init__(
            "Nigromante",
            Stats(
                320,
                320,
                48,
                64,
                6,
                magic_resist=10,
                speed=23,
                precision=12,
                evasion=6,
                crit_chance=0.08,
                crit_damage=1.6,
                magic_penetration=8,
            ),
            gold_min=110,
            gold_max=145,
        )

    def perform_turn(self, player) -> None:
        # Un turno de cada cinco, de media, convoca un esqueleto en vez de lanzar
        # su hechizo habitual: el no-muerto ataca de inmediato, cuerpo a cuerpo.
        if random.random() < 0.2:
            self._summon_undead(player)
        else:
            self._dark_bolt(player)

    def _dark_bolt(self, player) -> None:
        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(
                f"{console.colorize(self.name, console.Fore.MAGENTA)} lanza un dardo de energía oscura, "
                f"pero {console.colorize(player.name, console.Fore.GREEN)} lo esquiva."
            )
            return

        damage = self.get_attack_damage()
        is_crit = random.random() < self.stats.crit_chance
        if is_crit:
            damage = int(damage * self.stats.crit_damage)

        final_damage = player.take_damage(damage, is_magical=True, magic_penetration=self.stats.magic_penetration)

        if is_crit:
            print(console.colorize("¡Golpe crítico!", console.Fore.YELLOW, bright=True))
        print(
            f"{console.colorize(self.name, console.Fore.MAGENTA)} lanza un dardo de energía oscura y hace "
            f"{console.colorize(str(final_damage), console.Fore.MAGENTA)} de daño."
        )

    def _summon_undead(self, player) -> None:
        print(
            console.colorize(
                f"{self.name} traza un símbolo en el aire... ¡un esqueleto emerge de la tierra!", console.Fore.MAGENTA
            )
        )

        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(f"El esqueleto invocado ataca, pero {console.colorize(player.name, console.Fore.GREEN)} lo esquiva.")
            return

        damage = self.get_attack_damage()
        final_damage = player.take_damage(damage, armor_penetration=self.stats.armor_penetration)
        print(f"El esqueleto invocado hace {console.colorize(str(final_damage), console.Fore.RED)} de daño físico.")

    def drop_item(self) -> list:
        items = []
        if random.random() <= 0.5:
            items.append(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20))
        if random.random() <= 0.3:
            items.append(Material("Polvo de Hueso Negro", "Ceniza ósea impregnada de magia oscura.", 35, rarity="Raro"))
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Manto del Nigromante",
                    "Tejido con hilos que parecen absorber la luz de alrededor.",
                    60,
                    slot="amuleto",
                    magic_resist=10,
                    crit_chance=0.05,
                )
            )
        if random.random() <= 0.08:
            items.append(Weapon("Cetro de Huesos", "Rematado por un cráneo que aún parece susurrar.", 35, 25))
        if random.random() <= 0.06:
            items.append(
                Weapon(
                    "Cetro de Escarcha",
                    "El frío del más allá se filtra a través de su empuñadura.",
                    38,
                    21,
                    element="hielo",
                )
            )
        return items
