import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats, resolve_hit
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class GoblinMontaraz(Enemy):
    DESCRIPTION = "Explorador de los Yermos con más paciencia que sus primos: dispara antes de que lo veas."
    SIGNATURE = "Flechas certeras: sus disparos pueden abrirte una herida que sangra."
    ELEMENTS_DEALT = frozenset()
    INFLICTS = frozenset({"sangrado"})

    # Débil al fuego, como el resto de goblins del clan.
    WEAKNESSES = frozenset({"fuego"})

    def __init__(self):
        # Tirador: precisión y evasión por encima del Goblin normal, ataque un
        # punto más alto, pero nada excepcional en vida ni armadura.
        super().__init__(
            "Goblin Montaraz",
            Stats(48, 48, 8, 11, 2, speed=11, precision=9, evasion=3, crit_chance=0.06, crit_damage=1.5),
            gold_min=5,
            gold_max=7,
        )

    def perform_turn(self, player) -> None:
        """Ataque normal a distancia (misma tirada de acierto que cualquier otro
        golpe: esquivar una flecha sigue dependiendo de la evasión del jugador,
        no hay ningún truco especial aquí); a veces la punta deja una herida que
        sangra."""
        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(
                f"{console.colorize(self.name, console.Fore.RED)} dispara, pero "
                f"{console.colorize(player.name, console.Fore.GREEN)} esquiva la flecha."
            )
            return

        damage = self.get_attack_damage()
        is_crit = random.random() < self.stats.crit_chance
        if is_crit:
            damage = int(damage * self.stats.crit_damage)

        final_damage = player.take_damage(damage, armor_penetration=self.stats.armor_penetration)
        print(
            f"{console.colorize(self.name, console.Fore.RED)} dispara y hace "
            f"{console.colorize(str(final_damage), console.Fore.RED)} de daño."
            f"{console.crit_suffix(is_crit)}"
        )

        if random.random() < 0.25:
            player.apply_status("sangrado", 2)
            print(console.colorize("¡La flecha te ha abierto una herida!", console.Fore.LIGHTRED_EX))

    def drop_item(self) -> list:
        items = []
        if random.random() <= 0.6:
            items.append(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20))
        if random.random() <= 0.3:
            items.append(
                Material("Punta de Flecha", "Tallada en pedernal, todavía manchada de sangre seca.", 3, rarity="Común")
            )
        if random.random() <= 0.1:
            items.append(Weapon("Arco Corto", "Nudoso y curvado a mano, pero sorprendentemente certero.", 6, 4))
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Hombreras de Cazador",
                    "Curtidas para no delatar el movimiento al tensar el arco.",
                    13,
                    slot="hombreras",
                    precision=2,
                )
            )
        return items
