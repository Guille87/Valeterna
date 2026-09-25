import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats, resolve_hit
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class ElEnraizado(Enemy):
    DESCRIPTION = (
        "El guardián del Bosque de los Susurros. Lo que sea que ataron al altar hace tanto, sigue atado — y despierto."
    )
    SIGNATURE = "El Bosque Atado: maldice con cada golpe certero, y se cura mientras el altar siga alimentándolo."
    ELEMENTS_DEALT = frozenset({"oscuridad"})
    INFLICTS = frozenset({"maldicion"})

    # Tier 10 del Bosque (guardián): lo sagrado es lo único capaz de romper
    # una atadura así; su propia corrupción lo protege de la oscuridad y,
    # como lleva siglos alimentándose de algo que no es sangre, el veneno no
    # tiene nada a lo que aferrarse.
    WEAKNESSES = frozenset({"sagrado"})
    RESISTANCES = frozenset({"oscuridad", "veneno"})

    ENCOUNTER_KIND = "guardian"
    ENCOUNTER_LINE = (
        "Las raíces del claro se tensan bajo tus pies. Algo que lleva atado al altar más tiempo del "
        "que puedes imaginar, por fin, abre los ojos."
    )
    TAUNT_LINES = (
        "Todavía atado, todavía hambriento. Y tú, todavía aquí.",
        "El altar no suelta lo que ata. Tampoco te soltará a ti.",
        "Vuelves a la cadena que otros rompieron sin conseguirlo.",
    )

    def __init__(self):
        super().__init__(
            "El Enraizado",
            Stats(
                452,
                452,
                34,
                47,
                9,
                magic_resist=8,
                speed=11,
                precision=11,
                evasion=4,
                crit_chance=0.08,
                crit_damage=1.6,
                armor_penetration=4,
                magic_penetration=5,
            ),
            gold_min=190,
            gold_max=240,
        )

    def perform_turn(self, player) -> None:
        # Autocuración bajo el 40% de vida, igual de umbral que la furia de El
        # Carnicero, pero aquí es curación en vez de más daño.
        if self.stats.health <= (self.stats.max_health * 0.4) and random.random() < 0.35:
            self._self_heal()
            return

        self._dark_strike(player)

    def _self_heal(self) -> None:
        healed = self.heal(random.randint(35, 55))
        if healed <= 0:
            print(
                f"{console.colorize(self.name, console.Fore.MAGENTA)} tira de sus raíces, pero no queda nada que dar."
            )
            return
        print(
            f"{console.colorize(self.name, console.Fore.MAGENTA)} hunde sus raíces en el altar. "
            f"{console.colorize(f'+{healed} HP', console.Fore.GREEN)}."
        )

    def _dark_strike(self, player) -> None:
        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(
                f"{console.colorize(self.name, console.Fore.RED)} golpea con una rama oscurecida, pero "
                f"{console.colorize(player.name, console.Fore.GREEN)} logra esquivarla."
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
            f"{console.colorize(self.name, console.Fore.RED)} golpea con una rama oscurecida y hace "
            f"{console.colorize(str(final_damage), console.Fore.RED)} de daño."
            f"{console.crit_suffix(is_crit)}"
        )

        if random.random() < 0.3:
            player.apply_status("maldicion", duration=3, power=4)
            print(console.colorize("¡La atadura del altar se extiende hasta ti! -4 de armadura.", console.Fore.MAGENTA))

    def drop_item(self) -> list:
        items = []
        if random.random() <= 0.6:
            items.append(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20))
        if random.random() <= 0.3:
            items.append(
                Material(
                    "Raíz Atada", "Sigue retorciéndose muy despacio incluso arrancada del suelo.", 14, rarity="Raro"
                )
            )
        if random.random() <= 0.1:
            items.append(
                Weapon(
                    "Cetro Enraizado", "Una rama tallada que todavía intenta echar raíces.", 34, 23, element="oscuridad"
                )
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Cinturón de Raíces",
                    "Se ciñe solo, como si quisiera atar también a quien lo lleva.",
                    38,
                    slot="cinturon",
                    defense=6,
                    max_health=20,
                )
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Anillo del Enraizado",
                    "Tallado en el mismo material que el altar del claro.",
                    32,
                    slot="anillo",
                    crit_damage=0.08,
                )
            )
        return items
