import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats, resolve_hit
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class EspantajoAnegado(Enemy):
    DESCRIPTION = "Cañas, cuerda podrida y barro, atado en una forma que ya no debería sostenerse en pie."
    SIGNATURE = "Zarpazo de cañas: sus bordes afilados pueden abrir una herida que sigue sangrando."
    ELEMENTS_DEALT = frozenset()
    INFLICTS = frozenset({"sangrado"})
    ENCOUNTER_LINE = "Entre los juncos, algo que parecía un espantapájaros vuelve la cabeza hacia ti."

    def __init__(self):
        super().__init__(
            "Espantajo Anegado",
            Stats(
                525,
                525,
                20,
                27,
                13,
                magic_resist=1,
                speed=10,
                precision=8,
                evasion=2,
                crit_chance=0.06,
                crit_damage=1.5,
                armor_penetration=4,
            ),
            gold_min=160,
            gold_max=200,
        )

    def perform_turn(self, player) -> None:
        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(
                f"{console.colorize(self.name, console.Fore.RED)} golpea con sus cañas, pero "
                f"{console.colorize(player.name, console.Fore.GREEN)} logra esquivar."
            )
            return

        is_crit = random.random() < self.stats.crit_chance
        damage = self.get_max_attack_damage() if is_crit else self.get_attack_damage()
        if is_crit:
            damage = int(damage * self.stats.crit_damage)

        final_damage = player.take_damage(damage, armor_penetration=self.stats.armor_penetration)
        print(
            f"{console.colorize(self.name, console.Fore.RED)} zarpea y hace "
            f"{console.colorize(str(final_damage), console.Fore.RED)} de daño."
            f"{console.crit_suffix(is_crit)}"
        )

        if random.random() < 0.3:
            player.apply_status("sangrado", 3)
            print(console.colorize("¡Las cañas dejan un corte profundo!", console.Fore.RED))
            reaction_msg = player.pop_status_reaction_message()
            if reaction_msg:
                print(reaction_msg)

    def drop_item(self) -> list:
        items = []
        if random.random() <= 0.5:
            items.append(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20))
        if random.random() <= 0.3:
            items.append(
                Material("Fibra Anegada", "Cuerda vegetal empapada; no se pudre, solo se endurece.", 9, rarity="Común")
            )
        if random.random() <= 0.1:
            items.append(Weapon("Garra de Cañas", "Un manojo de cañas afiladas atadas en forma de zarpa.", 21, 13))
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Perneras de Junco",
                    "Trenzadas tan tupidas que apenas dejan pasar el agua.",
                    26,
                    slot="perneras",
                    evasion=4,
                )
            )
        return items
