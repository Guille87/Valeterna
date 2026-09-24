import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats, resolve_hit
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class ElSinRostro(Enemy):
    DESCRIPTION = (
        "«No he visto su rostro. Los ángeles caídos le sirven. Los demonios solo lo temen.» El Dragón arrasó "
        "Valeterna. Esto la gobierna desde entonces, y nadie ha vuelto a ver la diferencia."
    )
    SIGNATURE = "El Que Gobierna: se cura de la propia ruina que administra y maldice con cada golpe certero."
    ELEMENTS_DEALT = frozenset({"oscuridad"})
    INFLICTS = frozenset({"maldicion"})

    # Guardián de la Ciudadela en Ruinas: lo sagrado es lo único que
    # perturba a lo que ni ángeles ni demonios se atreven a nombrar; su
    # propia corrupción lo protege de la oscuridad.
    WEAKNESSES = frozenset({"sagrado"})
    RESISTANCES = frozenset({"oscuridad"})

    ENCOUNTER_KIND = "guardian"
    ENCOUNTER_LINE = (
        "Bajo la Catedral rota, algo que ni los ángeles caídos nombran ni los demonios se atreven a mirar, "
        "por fin sube a la superficie. El Sin Rostro no tiene nada que enseñarte, y aun así lo ves."
    )
    TAUNT_LINES = (
        "El Dragón quemó la ciudad. Yo la administro desde entonces.",
        "Ni ángel ni demonio se atreve a nombrarme. Tú tampoco podrás.",
        "Aldric cuenta los nombres de los que perdió. Yo ni siquiera los cuento.",
    )

    def __init__(self):
        super().__init__(
            "El Sin Rostro",
            Stats(
                1740,
                1740,
                54,
                71,
                20,
                magic_resist=18,
                speed=12,
                precision=15,
                evasion=7,
                crit_chance=0.10,
                crit_damage=1.7,
                armor_penetration=8,
                magic_penetration=10,
            ),
            gold_min=760,
            gold_max=910,
        )

    def perform_turn(self, player) -> None:
        # Autocuración bajo el 40% de vida, mismo umbral que los guardianes anteriores.
        if self.stats.health <= (self.stats.max_health * 0.4) and random.random() < 0.35:
            self._self_heal()
            return

        self._ruin_bolt(player)

    def _self_heal(self) -> None:
        healed = self.heal(random.randint(55, 80))
        if healed <= 0:
            print(
                f"{console.colorize(self.name, console.Fore.MAGENTA)} extiende su dominio, pero ya no queda ruina que dar."
            )
            return
        print(
            f"{console.colorize(self.name, console.Fore.MAGENTA)} absorbe la ruina que administra. "
            f"{console.colorize(f'+{healed} HP', console.Fore.GREEN)}."
        )

    def _ruin_bolt(self, player) -> None:
        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(
                f"{console.colorize(self.name, console.Fore.RED)} golpea sin forma definida, pero "
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
            f"{console.colorize(self.name, console.Fore.RED)} golpea sin forma definida y hace "
            f"{console.colorize(str(final_damage), console.Fore.RED)} de daño."
            f"{console.crit_suffix(is_crit)}"
        )

        if random.random() < 0.3:
            player.apply_status("maldicion", duration=3, power=5)
            print(console.colorize("¡Su dominio se extiende sobre tu armadura! -5 de armadura.", console.Fore.MAGENTA))

    def drop_item(self) -> list:
        items = []
        if random.random() <= 0.6:
            items.append(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20))
        if random.random() <= 0.3:
            items.append(
                Material(
                    "Fragmento Sin Rostro",
                    "No tiene forma fija; cambia cada vez que dejas de mirarlo.",
                    48,
                    rarity="Raro",
                )
            )
        if random.random() <= 0.1:
            items.append(
                Weapon(
                    "Cetro Sin Rostro",
                    "No tiene empuñadura reconocible, y aun así se sostiene bien.",
                    56,
                    38,
                    element="oscuridad",
                )
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Amuleto Sin Rostro",
                    "No refleja nada de quien lo lleva puesto.",
                    78,
                    slot="amuleto",
                    magic_resist=15,
                )
            )
        return items
