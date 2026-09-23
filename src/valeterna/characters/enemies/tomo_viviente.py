import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats, resolve_hit
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class TomoViviente(Enemy):
    DESCRIPTION = "Un grimorio que dejó de necesitar quien lo leyera. Sus páginas cortan tan bien como las palabras."
    SIGNATURE = "Corte de página: sus bordes pueden dejar una herida que sigue sangrando."
    ELEMENTS_DEALT = frozenset()
    INFLICTS = frozenset({"sangrado"})
    ENCOUNTER_LINE = (
        "Un libro se despega solo del estante y bate las tapas como si fueran alas. Un Tomo Viviente te encara."
    )

    # Tier 3 de la Torre: papel viejo arde muy bien.
    WEAKNESSES = frozenset({"fuego"})

    def __init__(self):
        super().__init__(
            "Tomo Viviente",
            Stats(
                855,
                855,
                32,
                43,
                14,
                magic_resist=6,
                speed=14,
                precision=12,
                evasion=8,
                crit_chance=0.07,
                crit_damage=1.6,
                armor_penetration=4,
            ),
            gold_min=360,
            gold_max=430,
        )

    def perform_turn(self, player) -> None:
        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(
                f"{console.colorize(self.name, console.Fore.RED)} bate las tapas, pero "
                f"{console.colorize(player.name, console.Fore.GREEN)} logra apartarse."
            )
            return

        is_crit = random.random() < self.stats.crit_chance
        damage = self.get_max_attack_damage() if is_crit else self.get_attack_damage()
        if is_crit:
            damage = int(damage * self.stats.crit_damage)

        final_damage = player.take_damage(damage, armor_penetration=self.stats.armor_penetration)
        print(
            f"{console.colorize(self.name, console.Fore.RED)} azota con sus páginas y hace "
            f"{console.colorize(str(final_damage), console.Fore.RED)} de daño."
            f"{console.crit_suffix(is_crit)}"
        )

        if random.random() < 0.3:
            player.apply_status("sangrado", 3)
            print(console.colorize("¡El filo de las páginas deja un corte profundo!", console.Fore.RED))
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
                    "Página Suelta",
                    "Las letras se reordenan solas si la miras demasiado tiempo.",
                    26,
                    rarity="Poco común",
                )
            )
        if random.random() <= 0.1:
            items.append(Weapon("Filo de Tapa Dura", "Arrancado del lomo de un libro que ya no lo necesitaba.", 37, 25))
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Yelmo de Cuero Viejo",
                    "Encuadernado como un libro; sigue oliendo a biblioteca.",
                    48,
                    slot="casco",
                    max_health=30,
                )
            )
        return items
