import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats, resolve_hit
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class ChispaDelPuntal(Enemy):
    DESCRIPTION = "Nació del mineral de tormenta que la cuadrilla desenterró antes del derrumbe. Nunca se ha apagado."
    SIGNATURE = "Descarga: su golpe conduce electricidad y puede dejarte paralizado."
    ELEMENTS_DEALT = frozenset({"rayo"})
    INFLICTS = frozenset({"paralizado"})
    ENCOUNTER_KIND = "elite"
    ENCOUNTER_LINE = "El aire chisporrotea antes de que la veas. Una Chispa del Puntal se condensa frente a ti."
    TAUNT_LINES = (
        "Ya sentiste mi descarga una vez. Esta vez no sueltas el arma.",
        "Nunca me he apagado. No empezaré contigo.",
    )

    # Tier 5 del Cañón (primer élite): ya está hecha de rayo puro, así que más
    # rayo no le añade nada; el hielo, en cambio, la apaga de golpe.
    WEAKNESSES = frozenset({"hielo"})
    IMMUNE_ELEMENTS = frozenset({"rayo"})
    IMMUNE_STATUSES = frozenset({"paralizado"})

    def __init__(self):
        super().__init__(
            "Chispa del Puntal",
            Stats(
                715,
                715,
                30,
                40,
                8,
                magic_resist=3,
                speed=13,
                precision=13,
                evasion=6,
                crit_chance=0.07,
                crit_damage=1.6,
                armor_penetration=6,
            ),
            gold_min=260,
            gold_max=310,
        )

    def perform_turn(self, player) -> None:
        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(
                f"{console.colorize(self.name, console.Fore.RED)} descarga, pero "
                f"{console.colorize(player.name, console.Fore.GREEN)} logra esquivarla."
            )
            return

        is_crit = random.random() < self.stats.crit_chance
        damage = self.get_max_attack_damage() if is_crit else self.get_attack_damage()
        if is_crit:
            damage = int(damage * self.stats.crit_damage)

        final_damage = player.take_damage(damage, armor_penetration=self.stats.armor_penetration, element="rayo")
        print(
            f"{console.colorize(self.name, console.Fore.RED)} descarga y hace "
            f"{console.colorize(str(final_damage), console.Fore.RED)} de daño."
            f"{console.crit_suffix(is_crit)}"
        )

        if random.random() < 0.25:
            player.apply_status("paralizado", 1)
            print(console.colorize("¡La descarga te deja paralizado!", console.Fore.YELLOW))

    def drop_item(self) -> list:
        items = []
        if random.random() <= 0.5:
            items.append(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20))
        if random.random() <= 0.3:
            items.append(
                Material("Mineral de Tormenta", "Sigue caliente y crepita cuando lo sostienes.", 20, rarity="Raro")
            )
        if random.random() <= 0.1:
            items.append(
                Weapon(
                    "Esquirla de Tormenta",
                    "Un fragmento de la propia chispa, cristalizado; sigue crepitando con la misma carga.",
                    32,
                    21,
                    element="rayo",
                )
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Brazales de Tormenta",
                    "Recorridos por venas de metal que aún conducen corriente.",
                    40,
                    slot="brazales",
                    crit_chance=0.05,
                )
            )
        return items
