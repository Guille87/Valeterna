import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats, resolve_hit
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class ChamanGoblin(Enemy):
    DESCRIPTION = "El único goblin del clan que sabe leer los símbolos del altar del Bosque, aunque no del todo bien."
    SIGNATURE = "Bendición oscura: se cura cuando está malherido y puede maldecir tu armadura."
    ELEMENTS_DEALT = frozenset({"oscuridad"})
    INFLICTS = frozenset({"maldicion"})
    ENCOUNTER_KIND = "elite"
    ENCOUNTER_LINE = "Un Chamán Goblin murmura algo entre dientes al verte llegar."
    TAUNT_LINES = (
        "La maldición no se olvida solo porque hayas vuelto.",
        "Los símbolos del altar no mienten: ibas a volver.",
    )

    # Débil a lo sagrado como el resto de su clan; su propio poder es oscuro,
    # así que lo resiste (mismo patrón que el Mago resistiendo arcano).
    WEAKNESSES = frozenset({"sagrado"})
    RESISTANCES = frozenset({"oscuridad"})

    def __init__(self):
        # Primer élite de Los Yermos: caster de apoyo, no pega fuerte pero se
        # cura y debilita al jugador.
        super().__init__(
            "Chamán Goblin",
            Stats(
                99, 99, 18, 28, 2, magic_resist=4, speed=13, precision=9, evasion=5, crit_chance=0.06, crit_damage=1.5
            ),
            gold_min=13,
            gold_max=17,
        )

    def perform_turn(self, player) -> None:
        # Autocuración bajo la mitad de vida, más frecuente que el Mago (30%)
        # porque su daño es más flojo y necesita alargar el combate.
        if self.stats.health <= (self.stats.max_health * 0.5) and random.random() < 0.3:
            self._self_heal()
            return

        # Un turno de cada cuatro, de media, maldice en vez de atacar.
        if random.random() < 0.25:
            self._cast_curse(player)
        else:
            self._dark_bolt(player)

    def _self_heal(self) -> None:
        healed = self.heal(random.randint(15, 25))
        if healed <= 0:
            print(f"{console.colorize(self.name, console.Fore.MAGENTA)} entona un cántico, pero no le sirve de nada.")
            return
        print(
            f"{console.colorize(self.name, console.Fore.MAGENTA)} entona un cántico oscuro. "
            f"{console.colorize(f'+{healed} HP', console.Fore.GREEN)}."
        )

    def _cast_curse(self, player) -> None:
        """Maldición menor: reduce la armadura efectiva del jugador (mismo
        estado que el Espíritu Vengativo, pero más floja: -2 en vez de -4, y
        solo 2 turnos)."""
        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(
                f"{console.colorize(self.name, console.Fore.MAGENTA)} intenta maldecir a "
                f"{console.colorize(player.name, console.Fore.GREEN)}, pero falla."
            )
            return

        player.apply_status("maldicion", duration=2, power=2)
        print(
            f"{console.colorize(self.name, console.Fore.MAGENTA)} traza un símbolo torcido. "
            f"{console.colorize('¡Maldito! -2 de armadura durante 2 turnos.', console.Fore.MAGENTA)}"
        )

    def _dark_bolt(self, player) -> None:
        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(
                f"{console.colorize(self.name, console.Fore.MAGENTA)} lanza un dardo oscuro, pero "
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
            f"{console.colorize(self.name, console.Fore.MAGENTA)} lanza un dardo oscuro y hace "
            f"{console.colorize(str(final_damage), console.Fore.MAGENTA)} de daño."
            f"{console.crit_suffix(is_crit)}"
        )

    def drop_item(self) -> list:
        items = []
        if random.random() <= 0.55:
            items.append(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20))
        if random.random() <= 0.3:
            items.append(
                Material(
                    "Huesos de Augur",
                    "Pequeños huesos tallados con símbolos que nadie más sabe leer.",
                    4,
                    rarity="Común",
                )
            )
        if random.random() <= 0.1:
            items.append(Weapon("Cayado Goblin", "Un palo nudoso rematado con un cráneo pequeño.", 11, 8))
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Amuleto de Hueso",
                    "Tallado con los mismos símbolos torcidos del cántico.",
                    16,
                    slot="amuleto",
                    magic_resist=2,
                )
            )
        return items
