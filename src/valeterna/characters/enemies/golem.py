import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class GolemDePiedra(Enemy):
    DESCRIPTION = "Coloso de roca nacido de la mina derrumbada. Nadie lo maneja; nadie sabe cómo pararlo."
    SIGNATURE = "Terremoto: de vez en cuando golpea el suelo y su ataque es imposible de esquivar."
    ELEMENTS_DEALT = frozenset()
    INFLICTS = frozenset()
    ENCOUNTER_KIND = "elite"
    ENCOUNTER_LINE = (
        "El suelo cruje bajo un peso imposible. El Gólem de Piedra se yergue ante ti, "
        "y toda la mina parece contener el aliento."
    )
    TAUNT_LINES = (
        "Golpea todo lo que quieras. La piedra no se cansa; tú sí.",
        "Ya has estado aquí. Y ya sabes cómo termina.",
    )

    # Mole de roca: el rayo se disipa en la tierra sin hacer nada (inmune, y por
    # tanto tampoco puede quedar paralizado), pero el hielo se cuela por las
    # grietas y las revienta al expandirse (débil).
    WEAKNESSES = frozenset({"hielo"})
    IMMUNE_ELEMENTS = frozenset({"rayo"})
    IMMUNE_STATUSES = frozenset({"paralizado"})

    def __init__(self):
        # Defensa casi impenetrable: la armadura más alta de todos los enemigos.
        super().__init__(
            "Gólem de Piedra",
            Stats(
                450,
                450,
                42,
                54,
                20,
                magic_resist=4,
                speed=12,
                precision=8,
                evasion=0,
                crit_chance=0.05,
                crit_damage=1.6,
                armor_penetration=12,
            ),
            gold_min=90,
            gold_max=120,
        )

    def perform_turn(self, player) -> None:
        # Un turno de cada cinco, de media, provoca un terremoto en vez de golpear:
        # sacude el suelo bajo los pies del jugador, así que no hay forma de esquivarlo.
        if random.random() < 0.2:
            self._earthquake(player)
        else:
            super().perform_turn(player)

    def _earthquake(self, player) -> None:
        print(console.colorize(f"¡{self.name} golpea el suelo con fuerza! La tierra tiembla...", console.Fore.RED))

        damage = self.get_attack_damage()
        final_damage = player.take_damage(damage, armor_penetration=self.stats.armor_penetration)
        print(
            f"El terremoto hace {console.colorize(str(final_damage), console.Fore.RED)} de daño. "
            f"{console.colorize('(imposible de esquivar)', console.Fore.BLACK, bright=True)}"
        )

    def drop_item(self) -> list:
        items = []
        if random.random() <= 0.5:
            items.append(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20))
        if random.random() <= 0.25:
            items.append(
                Material("Núcleo de Gólem", "Un núcleo de piedra pulida que aún retiene calor.", 30, rarity="Raro")
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Coraza de Gólem",
                    "Una plancha de roca maciza tallada para envolver el torso entero.",
                    55,
                    slot="peto",
                    defense=22,
                    max_health=30,
                )
            )
        if random.random() <= 0.08:
            items.append(
                Weapon("Mazo de Gólem", "Un fragmento del propio brazo del gólem, todavía duro como la roca.", 30, 21)
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Cinturón de Roca",
                    "Un anillo de piedra tallada que ancla al portador al suelo.",
                    30,
                    slot="cinturon",
                    defense=4,
                    max_health=20,
                )
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Hombreras de Gólem",
                    "Bloques de piedra tallados directamente del propio gólem.",
                    22,
                    slot="hombreras",
                    precision=4,
                    defense=4,
                )
            )
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Botas de Gólem",
                    "Pesadas losas de piedra; apenas dejan avanzar, pero casi nada las atraviesa.",
                    20,
                    slot="botas",
                    speed=1,
                    defense=3,
                    max_health=10,
                )
            )
        return items
