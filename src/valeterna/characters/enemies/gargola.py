import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats, resolve_hit
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class Gargola(Enemy):
    def __init__(self):
        # Tanque de piedra: mucha vida y armadura, muy lenta.
        super().__init__(
            "Gárgola",
            Stats(
                380,
                380,
                29,
                39,
                14,
                magic_resist=3,
                speed=9,
                precision=7,
                evasion=0,
                crit_chance=0.05,
                crit_damage=1.7,
                armor_penetration=8,
            ),
            gold_min=70,
            gold_max=95,
        )
        self.turns_taken = 0

    def perform_turn(self, player) -> None:
        self.turns_taken += 1
        # Cada 3 turnos, en vez de un zarpazo normal, embiste con todo su peso.
        if self.turns_taken % 3 == 0:
            self._charge_attack(player)
        else:
            super().perform_turn(player)

    def _charge_attack(self, player) -> None:
        print(console.colorize(f"{self.name} se prepara y carga con todo su peso...", console.Fore.RED))

        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(
                f"{console.colorize(self.name, console.Fore.RED)} embiste, pero "
                f"{console.colorize(player.name, console.Fore.GREEN)} logra apartarse."
            )
            return

        damage = int(self.get_attack_damage() * 1.8)
        final_damage = player.take_damage(damage, armor_penetration=self.stats.armor_penetration)
        print(
            f"¡Embestida! {console.colorize(self.name, console.Fore.RED)} hace "
            f"{console.colorize(str(final_damage), console.Fore.RED)} de daño."
        )

    def drop_item(self) -> list:
        items = []
        if random.random() <= 0.5:
            items.append(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20))
        if random.random() <= 0.25:
            items.append(
                Material(
                    "Fragmento de Gárgola",
                    "Un trozo de piedra tallada que sigue pesando como si estuviera viva.",
                    20,
                    rarity="Raro",
                )
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Placa de Gárgola",
                    "Losas de piedra ajustadas al cuerpo; casi imposible de perforar.",
                    40,
                    slot="peto",
                    defense=16,
                    max_health=25,
                )
            )
        if random.random() <= 0.08:
            items.append(Weapon("Puño de Piedra", "Un guantelete macizo arrancado de una gárgola caída.", 22, 19))
        if random.random() <= 0.06:
            items.append(
                Weapon(
                    "Garra de Tormenta",
                    "Conserva la carga estática de incontables tormentas sobre el campanario.",
                    26,
                    15,
                    element="rayo",
                )
            )
        return items
