import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats, resolve_hit
from valeterna.items.equipment import Armor
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class ElCarnicero(Enemy):
    DESCRIPTION = "El guardián de Los Yermos. Nadie sabe su nombre real; solo lo que deja tras de sí."
    SIGNATURE = "Furia: por debajo del 40% de vida sus golpes pegan más fuerte y sangran más a menudo."
    ELEMENTS_DEALT = frozenset()
    INFLICTS = frozenset({"sangrado"})

    # Frase de encuentro (v0.14.x, GDD §8.1 follow-up): primer guardián del
    # juego, así que su intro y sus provocaciones marcan el tono del resto.
    ENCOUNTER_KIND = "guardian"
    ENCOUNTER_LINE = (
        "Una sombra cruza el sendero hacia el Bosque y se detiene. "
        "El Carnicero no dice nada — solo levanta su cuchilla, manchada de todos los que lo intentaron antes que tú."
    )
    TAUNT_LINES = (
        "¿Otra vez tú? Esta vez no llegarás ni a la mitad.",
        "Vuelves a por más. Qué corta es la memoria del miedo.",
        "El Bosque puede esperar. Tú, no tanto.",
    )

    # Guardián, tier 10 de Los Yermos (GDD §4.6).
    WEAKNESSES = frozenset({"sagrado"})
    RESISTANCES = frozenset({"veneno"})

    def __init__(self):
        super().__init__(
            "El Carnicero",
            Stats(
                306,
                306,
                77,
                109,
                6,
                magic_resist=2,
                speed=8,
                precision=9,
                evasion=2,
                crit_chance=0.05,
                crit_damage=1.5,
                armor_penetration=5,
            ),
            gold_min=45,
            gold_max=58,
        )
        # A diferencia de la furia cíclica del Orco, esta es de un solo
        # sentido: una vez activada, dura el resto del combate.
        self.enraged = False

    def on_turn_end(self) -> None:
        if self.is_alive() and not self.enraged and self.stats.health <= self.stats.max_health * 0.4:
            self.enraged = True
            self.announce(
                console.colorize(
                    "😡 ¡El Carnicero entra en furia! Sus golpes se vuelven más brutales.",
                    console.Fore.RED,
                    bright=True,
                )
            )

    def perform_turn(self, player) -> None:
        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(
                f"{console.colorize(self.name, console.Fore.RED)} ataca, pero "
                f"{console.colorize(player.name, console.Fore.GREEN)} logra esquivarlo."
            )
            return

        is_crit = random.random() < self.stats.crit_chance
        damage = self.get_max_attack_damage() if is_crit else self.get_attack_damage()
        if self.enraged:
            damage = int(damage * 1.4)

        if is_crit:
            damage = int(damage * self.stats.crit_damage)

        final_damage = player.take_damage(damage, armor_penetration=self.stats.armor_penetration)
        print(
            f"{console.colorize(self.name, console.Fore.RED)} golpea con su cuchilla y hace "
            f"{console.colorize(str(final_damage), console.Fore.RED)} de daño."
            f"{console.crit_suffix(is_crit)}"
        )

        bleed_chance = 0.5 if self.enraged else 0.25
        if random.random() < bleed_chance:
            player.apply_status("sangrado", 3)
            print(console.colorize("¡La herida sangra sin parar!", console.Fore.LIGHTRED_EX))

    def drop_item(self) -> list:
        items = []
        if random.random() <= 0.6:
            items.append(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20))
        if random.random() <= 0.3:
            items.append(
                Material(
                    "Hueso de Carnicero",
                    "Astillado y afilado como si lo hubiese hecho a propósito.",
                    6,
                    rarity="Poco común",
                )
            )
        if random.random() <= 0.1:
            items.append(
                Armor(
                    "Peto del Carnicero",
                    "Cosido con retazos de todo lo que ha caído bajo su cuchilla.",
                    24,
                    slot="peto",
                    defense=6,
                    max_health=15,
                )
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Amuleto de Sangre",
                    "Late al ritmo de un corazón que ya no es el suyo.",
                    22,
                    slot="amuleto",
                    magic_resist=3,
                )
            )
        return items
