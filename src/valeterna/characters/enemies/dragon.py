import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats, resolve_hit
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class Dragon(Enemy):
    # El Dragón de Ceniza es una criatura de fuego: inmune a las llamas (y a
    # que lo quemen), pero el hielo es justo lo que su naturaleza no soporta.
    WEAKNESSES = frozenset({"hielo"})
    IMMUNE_ELEMENTS = frozenset({"fuego"})
    IMMUNE_STATUSES = frozenset({"quemado"})

    def __init__(self):
        # Jefe final: vida masiva y mucha evasión ("esquiva volando"), además
        # del aliento de fuego (daño + quemadura, daño a lo largo del tiempo).
        super().__init__(
            "Dragón",
            Stats(
                700,
                700,
                45,
                62,
                14,
                magic_resist=10,
                speed=26,
                precision=14,
                evasion=6,
                crit_chance=0.10,
                crit_damage=1.8,
                armor_penetration=6,
            ),
            gold_min=250,
            gold_max=320,
        )

    def perform_turn(self, player) -> None:
        # Un turno de cada cuatro, de media, aliento de fuego en vez de zarpazo/mordisco.
        if random.random() < 0.25:
            self._fire_breath(player)
        else:
            self._claw_attack(player)

    def _claw_attack(self, player) -> None:
        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(
                f"{console.colorize(self.name, console.Fore.RED)} ataca, pero "
                f"{console.colorize(player.name, console.Fore.GREEN)} logra esquivarlo."
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
            f"{console.colorize(self.name, console.Fore.RED)} zarpazo/mordisco: "
            f"{console.colorize(str(final_damage), console.Fore.RED)} de daño."
        )

    def _fire_breath(self, player) -> None:
        from valeterna.audio.resource_manager import ResourceManager

        ResourceManager().play_sfx("fireball")

        print(console.colorize(f"¡{self.name} inhala profundamente...!", console.Fore.RED, bright=True))

        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(
                f"El aliento de fuego arrasa el suelo, pero {console.colorize(player.name, console.Fore.GREEN)} "
                f"logra apartarse a tiempo."
            )
            return

        damage = self.get_attack_damage()
        final_damage = player.take_damage(
            damage, is_fire=True, armor_penetration=self.stats.armor_penetration, element="fuego"
        )
        print(f"¡Aliento de Fuego! {console.colorize(str(final_damage), console.Fore.RED)} de daño.")

        if random.random() < 0.6:
            player.apply_status("quemado", 3)
            console.error("¡Las llamas prenden tu ropa!")

    def drop_item(self) -> list:
        items = []
        if random.random() <= 0.6:
            items.append(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20))
        if random.random() <= 0.35:
            items.append(
                Material(
                    "Escama de Dragón", "Una escama del tamaño de un escudo, todavía caliente.", 60, rarity="Legendario"
                )
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Coraza de Escamas de Dragón",
                    "Forjada con escamas superpuestas; repele el fuego tanto como el acero.",
                    100,
                    slot="peto",
                    defense=24,
                    magic_resist=8,
                    max_health=40,
                )
            )
        if random.random() <= 0.1:
            items.append(
                Weapon(
                    "Colmillo de Dragón",
                    "Un colmillo curvo tallado en un arma; aún desprende calor.",
                    55,
                    32,
                    element="fuego",
                )
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Amuleto de Escama de Dragón",
                    "Una única escama pulida engarzada en un colgante de oro.",
                    50,
                    slot="amuleto",
                    magic_resist=12,
                    defense=3,
                    damage=3,
                )
            )
        return items
