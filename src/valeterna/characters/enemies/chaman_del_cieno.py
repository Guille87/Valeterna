import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats, resolve_hit
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class ChamanDelCieno(Enemy):
    DESCRIPTION = "Reza a lo que duerme bajo el templo hundido. A veces, algo le contesta."
    SIGNATURE = "Corrupción del cieno: se cura cuando está malherido y puede maldecir tu armadura."
    ELEMENTS_DEALT = frozenset({"oscuridad"})
    INFLICTS = frozenset({"maldicion"})
    ENCOUNTER_LINE = (
        "Una figura envuelta en juncos podridos murmura junto a la orilla. Un Chamán del Cieno te ha visto."
    )

    # Tier 4 de la Ciénaga (primer élite): venera lo mismo que corrompió el
    # Bosque, así que lo sagrado lo purga igual de bien.
    WEAKNESSES = frozenset({"sagrado"})
    RESISTANCES = frozenset({"oscuridad"})

    def __init__(self):
        super().__init__(
            "Chamán del Cieno",
            Stats(
                515,
                515,
                19,
                26,
                10,
                magic_resist=7,
                speed=12,
                precision=12,
                evasion=5,
                crit_chance=0.08,
                crit_damage=1.6,
                magic_penetration=4,
            ),
            gold_min=180,
            gold_max=220,
        )

    def perform_turn(self, player) -> None:
        # Autocuración bajo la mitad de vida, mismo patrón que el Druida Corrupto.
        if self.stats.health <= (self.stats.max_health * 0.5) and random.random() < 0.3:
            self._self_heal()
            return

        # Uno de cada cuatro turnos, de media, maldice en vez de atacar.
        if random.random() < 0.25:
            self._cast_curse(player)
        else:
            self._sludge_bolt(player)

    def _self_heal(self) -> None:
        healed = self.heal(random.randint(20, 32))
        if healed <= 0:
            print(f"{console.colorize(self.name, console.Fore.MAGENTA)} hunde las manos en el cieno, pero nada sube.")
            return
        print(
            f"{console.colorize(self.name, console.Fore.MAGENTA)} absorbe el limo negro del fondo. "
            f"{console.colorize(f'+{healed} HP', console.Fore.GREEN)}."
        )

    def _cast_curse(self, player) -> None:
        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(
                f"{console.colorize(self.name, console.Fore.MAGENTA)} intenta maldecir a "
                f"{console.colorize(player.name, console.Fore.GREEN)}, pero falla."
            )
            return

        player.apply_status("maldicion", duration=3, power=3)
        print(
            f"{console.colorize(self.name, console.Fore.MAGENTA)} traza un símbolo con barro negro. "
            f"{console.colorize('¡Maldito! -3 de armadura durante 3 turnos.', console.Fore.MAGENTA)}"
        )

    def _sludge_bolt(self, player) -> None:
        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(
                f"{console.colorize(self.name, console.Fore.MAGENTA)} lanza un grumo de cieno, pero "
                f"{console.colorize(player.name, console.Fore.GREEN)} lo esquiva."
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
            f"{console.colorize(self.name, console.Fore.MAGENTA)} lanza un grumo de cieno y hace "
            f"{console.colorize(str(final_damage), console.Fore.MAGENTA)} de daño."
            f"{console.crit_suffix(is_crit)}"
        )

    def drop_item(self) -> list:
        items = []
        if random.random() <= 0.5:
            items.append(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20))
        if random.random() <= 0.3:
            items.append(
                Material("Cieno Negro", "Denso y tibio incluso lejos del agua. No debería estarlo.", 9, rarity="Común")
            )
        if random.random() <= 0.1:
            items.append(
                Weapon(
                    "Vara del Cieno",
                    "Tallada con símbolos que se mueven si dejas de mirarlos.",
                    23,
                    15,
                    element="oscuridad",
                )
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Amuleto de Barro Negro",
                    "Late muy despacio, como si algo respirara dentro.",
                    27,
                    slot="amuleto",
                    magic_resist=5,
                )
            )
        return items
