import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats, resolve_hit
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class AngelCaido(Enemy):
    DESCRIPTION = "Luz corrupta de alas ennegrecidas; sirve a lo que ahora gobierna la Ciudadela."
    SIGNATURE = (
        "Juicio Divino: de vez en cuando lanza un golpe sagrado un 60 % más fuerte, y se cura cuando está malherido."
    )
    ELEMENTS_DEALT = frozenset({"sagrado"})
    INFLICTS = frozenset()

    # Conserva su naturaleza sagrada pese a la caída, pero esa misma caída —su
    # corrupción— es la grieta que la oscuridad explota.
    WEAKNESSES = frozenset({"oscuridad"})
    RESISTANCES = frozenset({"sagrado"})

    def __init__(self):
        # Divinidad corrupta: ataque habitual mágico, con autocuración y un
        # golpe de "Juicio" ocasional mucho más fuerte que lo normal.
        super().__init__(
            "Ángel Caído",
            Stats(
                380,
                380,
                44,
                60,
                8,
                magic_resist=12,
                speed=19,
                precision=14,
                evasion=10,
                crit_chance=0.08,
                crit_damage=1.6,
                magic_penetration=8,
            ),
            gold_min=140,
            gold_max=180,
        )

    def perform_turn(self, player) -> None:
        # Autocuración: menos frecuente y con un umbral más bajo que el Mago
        # (30% con vida <=40%, frente al 40% con <=50% del Mago) para no caer
        # en el mismo problema de retroalimentación con la velocidad.
        if self.stats.health <= (self.stats.max_health * 0.4) and random.random() < 0.3:
            self._self_heal()
            return

        # Un turno de cada seis o siete, de media, un Juicio Divino en vez del golpe habitual.
        if random.random() < 0.15:
            self._divine_judgment(player)
        else:
            self._holy_strike(player)

    def _self_heal(self) -> None:
        healed = self.heal(random.randint(30, 50))
        if healed <= 0:
            print(f"{console.colorize(self.name, console.Fore.YELLOW)} extiende las alas, pero la luz no acude.")
            return
        print(
            f"{console.colorize(self.name, console.Fore.YELLOW)} extiende las alas y se envuelve en luz. "
            f"{console.colorize(f'+{healed} HP', console.Fore.GREEN)}."
        )

    def _holy_strike(self, player) -> None:
        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(
                f"{console.colorize(self.name, console.Fore.YELLOW)} ataca, pero "
                f"{console.colorize(player.name, console.Fore.GREEN)} lo esquiva."
            )
            return

        damage = self.get_attack_damage()
        is_crit = random.random() < self.stats.crit_chance
        if is_crit:
            damage = int(damage * self.stats.crit_damage)

        final_damage = player.take_damage(
            damage, is_magical=True, magic_penetration=self.stats.magic_penetration, element="sagrado"
        )

        if is_crit:
            print(console.colorize("¡Golpe crítico!", console.Fore.YELLOW, bright=True))
        print(
            f"{console.colorize(self.name, console.Fore.YELLOW)} golpea con luz corrupta y hace "
            f"{console.colorize(str(final_damage), console.Fore.MAGENTA)} de daño."
        )

    def _divine_judgment(self, player) -> None:
        print(
            console.colorize(
                f"¡{self.name} alza los brazos! Un juicio divino desciende...", console.Fore.YELLOW, bright=True
            )
        )

        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(f"El juicio cae, pero {console.colorize(player.name, console.Fore.GREEN)} logra esquivarlo.")
            return

        damage = int(self.get_attack_damage() * 1.6)
        final_damage = player.take_damage(
            damage, is_magical=True, magic_penetration=self.stats.magic_penetration, element="sagrado"
        )
        print(f"¡Juicio Divino! {console.colorize(str(final_damage), console.Fore.MAGENTA)} de daño.")

    def drop_item(self) -> list:
        items = []
        if random.random() <= 0.5:
            items.append(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20))
        if random.random() <= 0.3:
            items.append(
                Material(
                    "Pluma Corrupta", "Una pluma blanca manchada de un negro que no debería existir.", 40, rarity="Raro"
                )
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Aureola Rota",
                    "Un fragmento de halo que aún desprende un calor antinatural.",
                    70,
                    slot="casco",
                    max_health=35,
                    defense=10,
                    magic_resist=8,
                )
            )
        if random.random() <= 0.08:
            items.append(
                Weapon(
                    "Espada Sagrada Corrupta", "Su filo brilla con una luz que quema al portador equivocado.", 40, 27
                )
            )
        if random.random() <= 0.1:
            items.append(
                Armor(
                    "Anillo de Juicio",
                    "Un aro dorado que pesa más de lo que debería.",
                    35,
                    slot="anillo",
                    crit_damage=0.14,
                    damage=4,
                    magic_resist=3,
                )
            )
        return items
