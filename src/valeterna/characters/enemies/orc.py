import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats, apply_mitigation, resolve_hit
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import StatBuffPotion
from valeterna.ui import console


class Orc(Enemy):
    # Piel gruesa curtida: el veneno le cuesta más hacer mella.
    RESISTANCES = frozenset({"veneno"})

    def __init__(self):
        super().__init__(
            "Orco",
            Stats(
                150,
                150,
                15,
                20,
                6,
                magic_resist=1,
                speed=9,
                precision=10,
                evasion=3,
                crit_chance=0.08,
                crit_damage=1.75,
                armor_penetration=3,
            ),
            gold_min=21,
            gold_max=29,
        )
        self.fury_active = False
        self.total_turns = 0  # Contador de turnos transcurridos

    def perform_turn(self, player) -> None:
        # Lógica de Furia simplificada
        if self.fury_active:
            console.error("¡El Orco está enfurecido!")

            if not resolve_hit(self.stats.precision, player.get_total_evasion()):
                print(
                    f"{console.colorize(self.name, console.Fore.RED)} ataca enfurecido, pero "
                    f"{console.colorize(player.name, console.Fore.GREEN)} esquiva el golpe."
                )
                return

            # 1. Obtenemos el daño aleatorio del Orco (con posibilidad de crítico)
            base_damage = self.get_attack_damage()
            is_crit = random.random() < self.stats.crit_chance
            if is_crit:
                base_damage = int(base_damage * self.stats.crit_damage)

            # 2. Calculamos cuánto daño pasaría la defensa total del jugador
            # (mismo suelo de daño mínimo que take_damage: nunca 0 por armadura).
            mitigation = player.get_total_armor() - self.stats.armor_penetration
            damage_after_def = apply_mitigation(base_damage, mitigation)

            # 3. Multiplicamos el resultado por 2
            final_dmg = damage_after_def * 2

            # 4. Aplicamos el daño directamente a la salud del jugador. Este golpe
            # no pasa por take_damage() (ya lleva la mitigación restada), así que
            # la reducción por "Defender" se aplica aquí a mano.
            if getattr(player, "defending", False) and final_dmg > 0:
                final_dmg //= 2
            player.stats.health -= final_dmg

            print(
                f"{console.colorize(self.name, console.Fore.RED)} lanza un golpe devastador y hace "
                f"{console.colorize(str(final_dmg), console.Fore.RED)} de daño."
                f"{console.crit_suffix(is_crit)}"
            )
        else:
            super().perform_turn(player)

    def on_turn_end(self) -> None:
        """Gestiona el ciclo de 3 turnos calma / 3 turnos furia."""
        self.total_turns += 1

        # Lógica de ciclo (usando el turno actual):
        # Turnos 1, 2, 3 -> Calma
        # Turnos 4, 5, 6 -> Furia
        # Turnos 7, 8, 9 -> Calma...

        # Determinamos en qué fase estamos:
        # (self.total_turns - 1) // 3 nos da 0 para (1,2,3), 1 para (4,5,6), 2 para (7,8,9)...
        fase_furia = (self.total_turns // 3) % 2 == 1

        # Lógica de ACTIVACIÓN: Después del tercer turno (al final del turno 3)
        if fase_furia and not self.fury_active:
            self.fury_active = True
            self.announce(
                console.colorize("😡 ¡El Orco se ha enfurecido! Sus ojos brillan en rojo...", console.Fore.RED)
            )

        # Lógica de DESACTIVACIÓN: Si está en furia, reducir duración
        elif not fase_furia and self.fury_active:
            self.fury_active = False
            self.announce(
                console.colorize("😴 El Orco parece haberse cansado y recupera la calma.", console.Fore.YELLOW)
            )

    def drop_item(self) -> list:
        items = []
        if random.random() <= 0.1:
            items.append(Weapon("Hacha de Batalla", "Un arma colosal de doble filo, manchada por mil batallas", 15, 12))
        if random.random() <= 0.6:
            # Usamos StatBuffPotion para la fuerza
            items.append(StatBuffPotion("Poción de Fuerza", "Aumenta el ataque temporalmente", 5, "max_atk", 5, 3))
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Peto de Orco",
                    "Placas de metal remachadas sobre cuero curtido.",
                    12,
                    slot="peto",
                    defense=7,
                    max_health=20,
                )
            )
        if random.random() <= 0.2:
            items.append(
                Material("Colmillo de Orco", "Un colmillo enorme, todavía manchado de sangre seca.", 6, rarity="Común")
            )
        if random.random() <= 0.08:
            items.append(
                Weapon(
                    "Espada Flamígera", "Una hoja que arde con un fuego que nunca se apaga.", 15, 10, element="fuego"
                )
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Brazales de Guerra",
                    "Pesados brazales de guerra pensados para golpear más fuerte, no para protegerse.",
                    20,
                    slot="brazales",
                    crit_chance=0.03,
                    damage=3,
                )
            )
        return items
