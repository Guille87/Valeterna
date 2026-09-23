import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats, resolve_hit
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class ElAnegado(Enemy):
    DESCRIPTION = (
        "La figura inmensa del relieve del templo hundido, la que las pequeñas figuras arrodilladas miraban "
        "hacia arriba. Más antigua que la Brecha. Oren nunca la ha visto. La ha sentido moverse bajo el bote."
    )
    SIGNATURE = "El Cieno Despierto: se cura mientras el agua le siga alimentando, y maldice con cada golpe certero."
    ELEMENTS_DEALT = frozenset({"oscuridad"})
    INFLICTS = frozenset({"maldicion"})

    # Guardián de la Ciénaga: lo sagrado es lo único que perturba algo tan
    # antiguo; su propia corrupción lo protege de la oscuridad, y lleva tanto
    # tiempo bajo el agua que el veneno ya no tiene nada nuevo que ofrecerle.
    WEAKNESSES = frozenset({"sagrado"})
    RESISTANCES = frozenset({"oscuridad"})
    IMMUNE_ELEMENTS = frozenset({"veneno"})
    IMMUNE_STATUSES = frozenset({"veneno"})

    ENCOUNTER_KIND = "guardian"
    ENCOUNTER_LINE = (
        "El agua de toda la ciénaga se queda quieta a la vez. Algo que llevaba mucho más tiempo que la Brecha "
        "esperando bajo el templo hundido, por fin, sale a la superficie."
    )
    TAUNT_LINES = (
        "El agua siempre sube. Tú también lo harás, pero no como esperas.",
        "Las figuras del relieve miraban hacia arriba. Ahora sé por qué.",
        "Oren cuenta a los que se cruza. A ti también te contará.",
    )

    def __init__(self):
        super().__init__(
            "El Anegado",
            Stats(
                605,
                605,
                25,
                34,
                18,
                magic_resist=9,
                speed=11,
                precision=12,
                evasion=4,
                crit_chance=0.08,
                crit_damage=1.6,
                armor_penetration=5,
                magic_penetration=6,
            ),
            gold_min=220,
            gold_max=260,
        )

    def perform_turn(self, player) -> None:
        # Autocuración bajo el 40% de vida, mismo umbral que El Enraizado.
        if self.stats.health <= (self.stats.max_health * 0.4) and random.random() < 0.35:
            self._self_heal()
            return

        self._drowned_strike(player)

    def _self_heal(self) -> None:
        healed = self.heal(random.randint(35, 55))
        if healed <= 0:
            print(
                f"{console.colorize(self.name, console.Fore.MAGENTA)} se hunde más en el cieno, pero no queda nada que dar."
            )
            return
        print(
            f"{console.colorize(self.name, console.Fore.MAGENTA)} absorbe el agua estancada a su alrededor. "
            f"{console.colorize(f'+{healed} HP', console.Fore.GREEN)}."
        )

    def _drowned_strike(self, player) -> None:
        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(
                f"{console.colorize(self.name, console.Fore.RED)} golpea con un brazo de cieno, pero "
                f"{console.colorize(player.name, console.Fore.GREEN)} logra esquivarlo."
            )
            return

        is_crit = random.random() < self.stats.crit_chance
        damage = self.get_max_attack_damage() if is_crit else self.get_attack_damage()
        if is_crit:
            damage = int(damage * self.stats.crit_damage)

        final_damage = player.take_damage(
            damage, is_magical=True, magic_penetration=self.stats.magic_penetration, element="oscuridad"
        )
        print(
            f"{console.colorize(self.name, console.Fore.RED)} golpea con un brazo de cieno y hace "
            f"{console.colorize(str(final_damage), console.Fore.RED)} de daño."
            f"{console.crit_suffix(is_crit)}"
        )

        if random.random() < 0.3:
            player.apply_status("maldicion", duration=3, power=4)
            print(console.colorize("¡El cieno se aferra a tu armadura! -4 de armadura.", console.Fore.MAGENTA))

    def drop_item(self) -> list:
        items = []
        if random.random() <= 0.6:
            items.append(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20))
        if random.random() <= 0.3:
            items.append(
                Material(
                    "Legado del Anegado",
                    "Sigue tibio mucho después de sacarlo del agua. No debería.",
                    16,
                    rarity="Raro",
                )
            )
        if random.random() <= 0.1:
            items.append(
                Weapon(
                    "Cetro del Anegado",
                    "Tallado en un material que no se corresponde con ninguna piedra conocida.",
                    36,
                    24,
                    element="oscuridad",
                )
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Anillo del Cieno",
                    "El barro que lo recubre nunca llega a secarse.",
                    34,
                    slot="anillo",
                    crit_damage=0.09,
                )
            )
        return items
