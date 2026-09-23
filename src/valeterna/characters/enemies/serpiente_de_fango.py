import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats, resolve_hit
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class SerpienteDeFango(Enemy):
    DESCRIPTION = "Nada bajo el barro sin dejar rastro y ataca antes de que se note que algo faltaba en la orilla."
    SIGNATURE = "Doble mordisco: a veces ataca dos veces seguidas, y su veneno es de los más fuertes de la ciénaga."
    ELEMENTS_DEALT = frozenset()
    INFLICTS = frozenset({"veneno"})
    ENCOUNTER_LINE = "El barro se abre en silencio. Una Serpiente de Fango ya está a medio camino de morderte."

    # Tier 6 de la Ciénaga: el fuego seca el fango antes de que pueda esconderse en él.
    WEAKNESSES = frozenset({"fuego"})

    def __init__(self):
        super().__init__(
            "Serpiente de Fango",
            Stats(
                500,
                500,
                18,
                25,
                11,
                magic_resist=1,
                speed=15,
                precision=11,
                evasion=8,
                crit_chance=0.07,
                crit_damage=1.5,
                armor_penetration=3,
            ),
            gold_min=195,
            gold_max=235,
        )

    def perform_turn(self, player) -> None:
        """Ataque normal; a veces muerde una segunda vez antes de que puedas reaccionar."""
        self._bite(player, extra=False)

        if self.is_alive() and player.is_alive() and random.random() < 0.3:
            print(console.colorize("¡La serpiente vuelve a atacar antes de que te repongas!", console.Fore.GREEN))
            self._bite(player, extra=True)

    def _bite(self, player, extra: bool) -> None:
        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(
                f"{console.colorize(self.name, console.Fore.RED)} se lanza, pero "
                f"{console.colorize(player.name, console.Fore.GREEN)} logra apartarse."
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

        if random.random() < 0.3:
            player.apply_status("veneno", 3)
            print(console.colorize("¡El veneno se extiende rápido por la herida!", console.Fore.GREEN))
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
                    "Escama de Fango", "Cubierta de barro seco que no acaba de desprenderse.", 10, rarity="Poco común"
                )
            )
        if random.random() <= 0.1:
            items.append(
                Weapon(
                    "Colmillo de Fango", "El veneno sigue fresco mucho después de arrancarlo.", 22, 14, element="veneno"
                )
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Botas de Escama",
                    "Se adaptan al barro como una segunda piel.",
                    30,
                    slot="botas",
                    speed=3,
                )
            )
        return items
