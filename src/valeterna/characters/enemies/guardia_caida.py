import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats, resolve_hit
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class GuardiaCaida(Enemy):
    DESCRIPTION = "Uno de los mil que Aldric perdió. La armadura sigue en pie mucho después de que dejara de importar."
    SIGNATURE = "Estocada doble: a veces ataca dos veces seguidas antes de que puedas reaccionar."
    ELEMENTS_DEALT = frozenset()
    INFLICTS = frozenset()
    ENCOUNTER_LINE = "Una armadura oxidada se endereza entre los escombros. Un Guardia Caída retoma su puesto."

    # Tier 4 de la Ciudadela: solo queda la armadura y el deber; lo sagrado
    # es lo único que lo libera de ambos.
    WEAKNESSES = frozenset({"sagrado"})

    def __init__(self):
        super().__init__(
            "Guardia Caída",
            Stats(
                1550,
                1550,
                50,
                66,
                20,
                magic_resist=7,
                speed=10,
                precision=12,
                evasion=2,
                crit_chance=0.06,
                crit_damage=1.6,
                armor_penetration=7,
            ),
            gold_min=580,
            gold_max=690,
        )

    def perform_turn(self, player) -> None:
        """Ataque normal; a veces enlaza una segunda estocada de inmediato."""
        self._sword_strike(player, extra=False)

        if self.is_alive() and player.is_alive() and random.random() < 0.3:
            print(console.colorize("¡Enlaza una segunda estocada de inmediato!", console.Fore.GREEN))
            self._sword_strike(player, extra=True)

    def _sword_strike(self, player, extra: bool) -> None:
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
            f"{console.colorize(self.name, console.Fore.RED)} estoca y hace "
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
                    "Placa Oxidada",
                    "El blasón sigue ahí, aunque ya nadie recuerde a qué casa pertenecía.",
                    39,
                    rarity="Poco común",
                )
            )
        if random.random() <= 0.1:
            items.append(
                Weapon(
                    "Espada de Guardia", "Una hoja de servicio, gastada por años de guardia y no de combate.", 48, 33
                )
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Peto de Guardia Caída",
                    "Abollado en el pecho, justo donde se lleva un escudo.",
                    68,
                    slot="peto",
                    defense=24,
                    max_health=30,
                )
            )
        return items
