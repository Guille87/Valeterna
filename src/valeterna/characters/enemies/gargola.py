import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats, resolve_hit
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class Gargola(Enemy):
    DESCRIPTION = "Centinela de piedra que vigila los pasos del cañón. Alguien la puso ahí; nadie recuerda quién."
    SIGNATURE = "Embestida: cada 3 turnos carga con todo su peso y golpea un 80 % más fuerte."
    ELEMENTS_DEALT = frozenset()
    INFLICTS = frozenset()
    ENCOUNTER_LINE = "Una estatua que no debería moverse... se mueve. Una Gárgola despierta ante ti."

    # Constructo de piedra animado por magia: sin sangre que envenenar, pero lo
    # arcano resquebraja el hechizo que la mantiene en pie.
    WEAKNESSES = frozenset({"arcano"})
    IMMUNE_ELEMENTS = frozenset({"veneno"})
    IMMUNE_STATUSES = frozenset({"veneno"})

    def __init__(self):
        # Tanque de piedra: mucha vida y armadura, muy lenta. Reforzada
        # (v0.14.0-f) para abrir hueco de poder real a los 10 enemigos nuevos
        # de la Ciénaga de los Ahogados, que se insertan justo antes en la
        # cadena de desbloqueo — ver TODO.md.
        super().__init__(
            "Gárgola",
            Stats(
                575,
                575,
                34,
                46,
                18,
                magic_resist=4,
                speed=9,
                precision=8,
                evasion=0,
                crit_chance=0.05,
                crit_damage=1.7,
                armor_penetration=10,
            ),
            gold_min=110,
            gold_max=145,
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
